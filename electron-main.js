const { app, BrowserWindow, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');

let mainWindow;
let backendProcess;
let frontendProcess;

// Configuration
const BACKEND_PORT = 8001;
const FRONTEND_PORT = 3000;

// Utility function to wait for server
function waitForServer(url, maxAttempts = 30, interval = 1000) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    
    const checkServer = () => {
      attempts++;
      console.log(`Checking server at ${url} (attempt ${attempts}/${maxAttempts})`);
      
      http.get(url, (res) => {
        console.log(`✅ Server responded with status: ${res.statusCode}`);
        resolve(true);
      }).on('error', (err) => {
        if (attempts >= maxAttempts) {
          console.log(`❌ Server not ready after ${maxAttempts} attempts`);
          resolve(false); // Don't reject, just continue
        } else {
          setTimeout(checkServer, interval);
        }
      });
    };
    
    checkServer();
  });
}

// Start the Python FastAPI backend with Supabase
function startBackend() {
  return new Promise((resolve, reject) => {
    console.log('🚀 Starting PAC backend server with Supabase...');
    
    // Read DATABASE_URL from .env file
    const envPath = path.join(__dirname, '.env');
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
      console.error('❌ DATABASE_URL not found in .env file');
      reject(new Error('Database configuration missing'));
      return;
    }
    
    console.log('🗄️  Using Supabase PostgreSQL database');
    
    // Environment variables for backend
    const env = {
      ...process.env,
      DATABASE_URL: databaseUrl,
      PORT: BACKEND_PORT.toString(),
      HOST: '127.0.0.1',
      SECRET_KEY: 'pac-desktop-secret-key-' + Date.now(),
      USE_MEMORY_CACHE: 'true',
      STORAGE_PATH: path.join(app.getPath('userData'), 'storage'),
      DISABLE_LIFESPAN: 'false',
      SERVERLESS_MODE: 'false',
      IMAGE_PROCESSING_THREADS: '2',
      BACKGROUND_TASK_THREADS: '2',
      CACHE_SIZE: '100',
      DB_POOL_MIN_CONN: '1',
      DB_POOL_MAX_CONN: '5'
    };
    
    // Create storage directory
    const storageDir = env.STORAGE_PATH;
    if (!fs.existsSync(storageDir)) {
      fs.mkdirSync(storageDir, { recursive: true });
    }
    
    // Start backend using uvicorn
    console.log('📦 Starting backend with uvicorn...');
    backendProcess = spawn('uvicorn', [
      'backend.server_postgresql_fully_optimized:app',
      '--host', '127.0.0.1',
      '--port', BACKEND_PORT.toString(),
      '--reload'
    ], {
      env: env,
      cwd: __dirname,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let backendReady = false;
    
    backendProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      console.log('Backend:', output);
      
      // Check for startup success messages
      if (output.includes('Uvicorn running on') || 
          output.includes('Application startup complete') ||
          output.includes('Started server process')) {
        backendReady = true;
      }
    });
    
    backendProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      console.log('Backend Log:', output);
      
      // Also check stderr for startup messages
      if (output.includes('Uvicorn running on') || 
          output.includes('Application startup complete')) {
        backendReady = true;
      }
    });
    
    backendProcess.on('error', (error) => {
      console.error('❌ Failed to start backend:', error.message);
      reject(error);
    });
    
    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });
    
    // Wait for backend to start
    setTimeout(async () => {
      const serverReady = await waitForServer(`http://127.0.0.1:${BACKEND_PORT}/health`);
      if (serverReady || backendReady) {
        console.log('✅ Backend is ready!');
        resolve();
      } else {
        console.log('⚠️  Backend may not be fully ready, but continuing...');
        resolve(); // Continue anyway
      }
    }, 8000); // Give it 8 seconds
  });
}

// Start the React frontend
function startFrontend() {
  return new Promise((resolve, reject) => {
    console.log('🌐 Starting React frontend server...');
    
    const frontendDir = path.join(__dirname, 'frontend');
    
    if (!fs.existsSync(frontendDir)) {
      console.error('❌ Frontend directory not found:', frontendDir);
      reject(new Error('Frontend directory missing'));
      return;
    }
    
    // Environment variables for frontend
    const env = {
      ...process.env,
      PORT: FRONTEND_PORT.toString(),
      BROWSER: 'none', // Don't auto-open browser
      REACT_APP_API_URL: `http://127.0.0.1:${BACKEND_PORT}`,
      WDS_SOCKET_PORT: '0' // Disable webpack dev server overlay
    };
    
    // Start React development server
    console.log('📦 Starting React with npm start...');
    
    // Handle Windows command execution properly
    const isWindows = process.platform === 'win32';
    let frontendCmd, frontendArgs;
    
    if (isWindows) {
      frontendCmd = 'cmd.exe';
      frontendArgs = ['/c', 'npm', 'start'];
    } else {
      frontendCmd = 'npm';
      frontendArgs = ['start'];
    }
    
    console.log(`Running: ${frontendCmd} ${frontendArgs.join(' ')}`);
    
    frontendProcess = spawn(frontendCmd, frontendArgs, {
      cwd: frontendDir,
      env: env,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let frontendReady = false;
    
    frontendProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      console.log('Frontend:', output);
      
      // Check for successful startup
      if (output.includes('webpack compiled') || 
          output.includes('compiled successfully') ||
          output.includes('Local:') ||
          output.includes('On Your Network:')) {
        frontendReady = true;
      }
    });
    
    frontendProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      if (output && !output.includes('Warning:')) {
        console.log('Frontend Warning:', output);
      }
    });
    
    frontendProcess.on('error', (error) => {
      console.error('❌ Failed to start frontend:', error.message);
      reject(error);
    });
    
    frontendProcess.on('close', (code) => {
      console.log(`Frontend process exited with code ${code}`);
    });
    
    // Wait for frontend to be ready
    setTimeout(async () => {
      const serverReady = await waitForServer(`http://127.0.0.1:${FRONTEND_PORT}`);
      if (serverReady || frontendReady) {
        console.log('✅ Frontend is ready!');
        resolve();
      } else {
        console.log('⚠️  Frontend may not be fully ready, but continuing...');
        resolve(); // Continue anyway
      }
    }, 30000); // Give it 30 seconds for React to compile
  });
}

// Create the main Electron window
function createWindow() {
  console.log('🖥️  Creating PAC System window...');
  
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
    autoHideMenuBar: false, // Keep menu bar for debugging
    icon: path.join(__dirname, 'assets', 'icon.png')
  });
  
  // Load the React frontend
  const frontendUrl = `http://127.0.0.1:${FRONTEND_PORT}`;
  
  console.log('🔗 Loading frontend URL:', frontendUrl);
  
  mainWindow.loadURL(frontendUrl).then(() => {
    console.log('✅ Frontend loaded in Electron window');
    mainWindow.show();
  }).catch((error) => {
    console.error('❌ Failed to load frontend in Electron:', error.message);
    console.log('🌐 Opening in external browser instead...');
    
    // Fallback: open in system browser
    shell.openExternal(frontendUrl);
    
    // Show a simple info window
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
  
  // Add some useful shortcuts
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.control && input.key === 'r') {
      mainWindow.reload();
    }
  });
}

// Show startup progress
async function showStartupProgress() {
  const progressWindow = new BrowserWindow({
    width: 400,
    height: 300,
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
        <h2>🏥 PAC System</h2>
        <p>Starting Medical Image Management System...</p>
        <div style="margin: 20px 0;">
          <div style="width: 100%; background: #333; border-radius: 10px; height: 10px;">
            <div id="progress" style="width: 0%; background: #007acc; height: 100%; border-radius: 10px; transition: width 0.5s;"></div>
          </div>
        </div>
        <p id="status">Initializing...</p>
        <script>
          let progress = 0;
          const progressBar = document.getElementById('progress');
          const status = document.getElementById('status');
          
          const steps = [
            'Connecting to Supabase...',
            'Starting backend server...',
            'Loading React frontend...',
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
  console.log('🎯 PAC System Desktop starting...');
  console.log('🗄️  Database: Supabase PostgreSQL');
  
  // Show progress window
  const progressWindow = await showStartupProgress();
  
  try {
    // Start backend first
    console.log('1️⃣ Starting backend...');
    await startBackend();
    
    // Then start frontend
    console.log('2️⃣ Starting frontend...');
    await startFrontend();
    
    // Close progress window and create main window
    progressWindow.close();
    console.log('3️⃣ Creating main window...');
    createWindow();
    
    // Show success message
    console.log('🎉 PAC System started successfully!');
    console.log('🌐 Frontend: http://127.0.0.1:' + FRONTEND_PORT);
    console.log('🚀 Backend API: http://127.0.0.1:' + BACKEND_PORT);
    console.log('🗄️  Database: Supabase (Connected)');
    
  } catch (error) {
    console.error('❌ Startup failed:', error.message);
    
    progressWindow.close();
    
    // Show error dialog
    const errorChoice = await dialog.showMessageBox(null, {
      type: 'error',
      buttons: ['Open in Browser Anyway', 'Exit'],
      defaultId: 0,
      title: 'PAC System Startup Error',
      message: 'Failed to start some components',
      detail: `Error: ${error.message}\n\nYou can try opening the application in your browser manually.`
    });
    
    if (errorChoice.response === 0) {
      // Try to open in browser anyway
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

// Clean up processes
function cleanup() {
  console.log('🧹 Cleaning up...');
  
  if (backendProcess) {
    console.log('Stopping backend process...');
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
  
  if (frontendProcess) {
    console.log('Stopping frontend process...');
    frontendProcess.kill('SIGTERM');
    frontendProcess = null;
  }
  
  console.log('✅ Cleanup complete');
}
