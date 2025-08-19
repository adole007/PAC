const { app, BrowserWindow, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');
const express = require('express');

let mainWindow;
let backendProcess;
let frontendServer;

// Configuration
const BACKEND_PORT = 8001;
const FRONTEND_PORT = 3000;

// Get resource paths - works for both development and packaged app
function getResourcePath(relativePath) {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, relativePath);
  } else {
    // For development, check if we're looking for the backend executable
    if (relativePath === 'pac_backend.exe') {
      return path.join(__dirname, 'dist', 'pac_backend.exe');
    }
    return path.join(__dirname, relativePath);
  }
}

// Utility function to wait for server
function waitForServer(url, maxAttempts = 30, interval = 1000) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    
    const checkServer = () => {
      attempts++;
      console.log(`Checking server at ${url} (attempt ${attempts}/${maxAttempts})`);
      
      http.get(url, (res) => {
        console.log(`Server responded with status: ${res.statusCode}`);
        resolve(true);
      }).on('error', (err) => {
        if (attempts >= maxAttempts) {
          console.log(`Server not ready after ${maxAttempts} attempts`);
          resolve(false);
        } else {
          setTimeout(checkServer, interval);
        }
      });
    };
    
    checkServer();
  });
}

// Start the standalone backend executable
function startBackend() {
  return new Promise((resolve, reject) => {
    console.log('Starting PAC standalone backend...');
    
    const backendPath = getResourcePath('pac_backend.exe');
    const envPath = getResourcePath('.env');
    
    if (!fs.existsSync(backendPath)) {
      console.error('Backend executable not found:', backendPath);
      reject(new Error('Backend executable missing'));
      return;
    }
    
    // Read DATABASE_URL from .env file
    let databaseUrl = '';
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf8');
      const envLines = envContent.split('\n');
      envLines.forEach(line => {
        const [key, value] = line.split('=');
        if (key && value && key.trim() === 'DATABASE_URL') {
          databaseUrl = value.trim();
        }
      });
    }
    
    if (!databaseUrl) {
      console.error('DATABASE_URL not found in .env file');
      reject(new Error('Database configuration missing'));
      return;
    }
    
    console.log('Using Supabase PostgreSQL database');
    
    // Environment variables for backend
    const env = {
      ...process.env,
      DATABASE_URL: databaseUrl,
      PORT: BACKEND_PORT.toString(),
      HOST: '127.0.0.1',
      SECRET_KEY: 'pac-desktop-secret-key-' + Date.now(),
      USE_MEMORY_CACHE: 'true',
      STORAGE_PATH: path.join(app.getPath('userData'), 'storage'),
      STANDALONE_MODE: 'true',
      DISABLE_LIFESPAN: 'false',
      SERVERLESS_MODE: 'false'
    };
    
    // Create storage directory
    const storageDir = env.STORAGE_PATH;
    if (!fs.existsSync(storageDir)) {
      fs.mkdirSync(storageDir, { recursive: true });
    }
    
    console.log('Starting backend executable...');
    backendProcess = spawn(backendPath, [], {
      env: env,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let backendReady = false;
    
    backendProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      console.log('Backend:', output);
      
      if (output.includes('Starting PAC Backend') || 
          output.includes('Uvicorn running on') ||
          output.includes('Application startup complete')) {
        backendReady = true;
      }
    });
    
    backendProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      console.log('Backend Log:', output);
    });
    
    backendProcess.on('error', (error) => {
      console.error('Failed to start backend:', error.message);
      reject(error);
    });
    
    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });
    
    // Wait for backend to start
    setTimeout(async () => {
      const serverReady = await waitForServer(`http://127.0.0.1:${BACKEND_PORT}/health`);
      if (serverReady || backendReady) {
        console.log('Backend is ready!');
        resolve();
      } else {
        console.log('Backend may not be fully ready, but continuing...');
        resolve();
      }
    }, 8000);
  });
}

// Start the static frontend server
function startFrontend() {
  return new Promise((resolve, reject) => {
    console.log('Starting static frontend server...');
    
    const buildPath = getResourcePath('frontend/build');
    
    if (!fs.existsSync(buildPath)) {
      console.error('Frontend build directory not found:', buildPath);
      reject(new Error('Frontend build missing'));
      return;
    }
    
    try {
      // Create Express server to serve static files
      const expressApp = express();
      
      // Serve static files from React build
      expressApp.use(express.static(buildPath));
      
      // Handle React Router - serve index.html for all routes
      expressApp.get('*', (req, res) => {
        try {
          res.sendFile(path.join(buildPath, 'index.html'));
        } catch (err) {
          console.error('Error serving index.html:', err);
          res.status(500).send('Error loading application');
        }
      });
      
      frontendServer = expressApp.listen(FRONTEND_PORT, '127.0.0.1', (error) => {
        if (error) {
          console.error('Failed to start frontend server:', error);
          reject(error);
        } else {
          console.log(`Frontend server running on http://127.0.0.1:${FRONTEND_PORT}`);
          resolve();
        }
      });
    } catch (error) {
      console.error('Error setting up Express server:', error);
      reject(error);
    }
  });
}

// Create the main Electron window
function createWindow() {
  console.log('Creating PAC System window...');
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true
    },
    title: 'PAC System - Medical Image Management',
    show: false,
    autoHideMenuBar: false,
    icon: path.join(__dirname, 'assets', 'icon.png')
  });
  
  const frontendUrl = `http://127.0.0.1:${FRONTEND_PORT}`;
  
  console.log('Loading frontend URL:', frontendUrl);
  
  mainWindow.loadURL(frontendUrl).then(() => {
    console.log('Frontend loaded in Electron window');
    mainWindow.show();
  }).catch((error) => {
    console.error('Failed to load frontend in Electron:', error.message);
    
    // Fallback: open in system browser
    shell.openExternal(frontendUrl);
    
    // Show info window
    const infoHtml = `
      <html>
        <body style="font-family: Arial; padding: 20px; text-align: center;">
          <h1>PAC System</h1>
          <p>The application has opened in your default browser.</p>
          <p><a href="${frontendUrl}">Click here if it didn't open automatically</a></p>
          <p>Backend: <a href="http://127.0.0.1:${BACKEND_PORT}/health">http://127.0.0.1:${BACKEND_PORT}</a></p>
          <p>Frontend: <a href="${frontendUrl}">${frontendUrl}</a></p>
        </body>
      </html>
    `;
    
    mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(infoHtml)}`);
    mainWindow.show();
  });
  
  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
  
  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
  
  // Add keyboard shortcuts
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.control && input.key === 'r') {
      mainWindow.reload();
    }
  });
}

// Show startup progress
async function showStartupProgress() {
  const progressWindow = new BrowserWindow({
    width: 450,
    height: 350,
    show: true,
    frame: false,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  
  const progressHtml = `
    <html>
      <body style="font-family: Arial; padding: 30px; text-align: center; background: #1a1a1a; color: white;">
        <h2>PAC System - Self-Contained</h2>
        <p>Starting Medical Image Management System...</p>
        <p style="font-size: 12px; color: #888;">All dependencies bundled - no external requirements!</p>
        <div style="margin: 20px 0;">
          <div style="width: 100%; background: #333; border-radius: 10px; height: 10px;">
            <div id="progress" style="width: 0%; background: #007acc; height: 100%; border-radius: 10px; transition: width 0.5s;"></div>
          </div>
        </div>
        <p id="status">Initializing standalone components...</p>
        <script>
          let progress = 0;
          const progressBar = document.getElementById('progress');
          const status = document.getElementById('status');
          
          const steps = [
            'Loading backend executable...',
            'Starting FastAPI server...',
            'Serving static frontend...',
            'Ready to launch!'
          ];
          
          function updateProgress() {
            if (progress < 90) {
              progress += Math.random() * 20;
              progressBar.style.width = progress + '%';
              status.textContent = steps[Math.floor(progress / 25)];
              setTimeout(updateProgress, 1000 + Math.random() * 2000);
            }
          }
          
          updateProgress();
        </script>
      </body>
    </html>
  `;
  
  progressWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(progressHtml)}`);
  
  return progressWindow;
}

// Main app initialization
app.whenReady().then(async () => {
  console.log('PAC System Self-Contained Desktop starting...');
  console.log('Mode: Fully bundled with all dependencies');
  console.log('Database: Supabase PostgreSQL (Remote)');
  
  const progressWindow = await showStartupProgress();
  
  try {
    // Start backend executable
    console.log('Step 1: Starting standalone backend...');
    await startBackend();
    
    // Start static frontend
    console.log('Step 2: Starting static frontend...');
    await startFrontend();
    
    // Close progress and create main window
    progressWindow.close();
    console.log('Step 3: Creating main window...');
    createWindow();
    
    console.log('PAC System started successfully!');
    console.log('Frontend: http://127.0.0.1:' + FRONTEND_PORT);
    console.log('Backend API: http://127.0.0.1:' + BACKEND_PORT);
    console.log('Mode: Self-contained (no external dependencies)');
    
  } catch (error) {
    console.error('Startup failed:', error.message);
    
    progressWindow.close();
    
    const errorChoice = await dialog.showMessageBox(null, {
      type: 'error',
      buttons: ['Open in Browser Anyway', 'Exit'],
      defaultId: 0,
      title: 'PAC System Startup Error',
      message: 'Failed to start some components',
      detail: `Error: ${error.message}\n\nYou can try opening the application in your browser manually.`
    });
    
    if (errorChoice.response === 0) {
      createWindow();
    } else {
      app.quit();
    }
  }
});

// Handle app quit events
app.on('window-all-closed', () => {
  cleanup();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  cleanup();
});

// Clean up processes and servers
function cleanup() {
  console.log('Cleaning up...');
  
  if (backendProcess) {
    console.log('Stopping backend process...');
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
  
  if (frontendServer) {
    console.log('Stopping frontend server...');
    frontendServer.close();
    frontendServer = null;
  }
  
  console.log('Cleanup complete');
}
