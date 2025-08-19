# PAC Desktop Application

A desktop version of the PAC Medical Image Management System that runs on any laptop with **Supabase connectivity**.

## 🎯 What This Does

This desktop app:
- ✅ **Connects to your existing Supabase database** (same data as web version)
- ✅ **Runs your Python FastAPI backend locally** (port 8001)
- ✅ **Runs your React frontend locally** (port 3000)  
- ✅ **Opens in a desktop window or browser**
- ✅ **Works on Windows, Mac, and Linux**
- ✅ **All data synced with your web version**

## 🚀 Quick Start

### Option 1: Simple Run (Recommended)
1. **Double-click `run-pac-desktop.bat`** (Windows) 
2. The script will automatically:
   - Check and install dependencies
   - Start the backend and frontend
   - Open the application

### Option 2: Manual Run
```bash
# Install dependencies (first time only)
npm install
cd frontend && npm install --legacy-peer-deps && cd ..

# Start the desktop app
npm start
```

## 📋 Requirements

### Required Software
- **Node.js** (v16 or later) - [Download here](https://nodejs.org/)
- **Python** (v3.8 or later) with pip
- **Git** (optional, for updates)

### Required Python Packages
The batch file will auto-install these, or install manually:
```bash
pip install uvicorn fastapi psycopg2-binary python-jose passlib bcrypt python-multipart aiofiles pillow pydicom numpy aioredis python-dotenv
```

## 🗄️ Database Connection

The app connects to your **Supabase PostgreSQL database** using the `.env` file:
```
DATABASE_URL=postgresql://postgres.fjmlshmkdaufqkefmixw:jajuwa%40pac%40@aws-0-eu-north-1.pooler.supabase.com:5432/postgres
```

**Benefits:**
- ✅ Same data across web and desktop versions
- ✅ Real-time sync between devices
- ✅ Automatic backups via Supabase
- ✅ No local database setup needed

## 🏃‍♂️ How It Works

1. **Backend Server**: Starts Python FastAPI backend on `http://127.0.0.1:8001`
2. **Frontend Server**: Starts React development server on `http://127.0.0.1:3000`
3. **Database**: Connects to Supabase PostgreSQL (remote)
4. **Window**: Opens Electron window or browser tab

## 🔧 Development vs Production

### Development Mode
```bash
npm run electron-dev
```
- React development server (hot reload)
- Python backend with reload
- Debug tools enabled

### Production Mode
```bash
npm start
```
- Optimized for desktop use
- Better performance
- Cleaner interface

## 📦 Building Executable

To create a distributable executable:

### Windows
```bash
npm run dist
```
Creates: `dist/PAC Medical System Setup 1.0.0.exe` and portable version

### Mac  
```bash
npm run dist
```
Creates: `dist/PAC Medical System-1.0.0.dmg`

### Linux
```bash
npm run dist
```  
Creates: `dist/PAC Medical System-1.0.0.AppImage` and `.deb`

## 🌐 Access URLs

When running:
- **Frontend (User Interface)**: http://127.0.0.1:3000
- **Backend API**: http://127.0.0.1:8001
- **API Health Check**: http://127.0.0.1:8001/health
- **Database**: Supabase (cloud)

## 🔐 Login Credentials

Use the same credentials as your web version:
- **Username**: `admin`
- **Password**: `admin123`

(Or any other users you've created)

## 🐛 Troubleshooting

### Backend Won't Start
- Check if Python and uvicorn are installed: `uvicorn --version`
- Verify .env file exists with DATABASE_URL
- Check port 8001 isn't in use: `netstat -an | findstr 8001`

### Frontend Won't Start
- Check if Node.js is installed: `node --version`
- Clear cache: Delete `frontend/node_modules` and run `npm install --legacy-peer-deps`
- Check port 3000 isn't in use

### Database Connection Issues
- Verify internet connection (Supabase requires internet)
- Check DATABASE_URL in .env file
- Test connection: Visit http://127.0.0.1:8001/health

### Can't Install Dependencies
- Run Command Prompt as Administrator (Windows)
- Update npm: `npm install -g npm@latest`
- Try: `npm install --force` or `npm install --legacy-peer-deps`

## 📁 File Structure

```
PAC/
├── electron-main.js           # Main Electron process
├── package.json              # Node.js dependencies & build config
├── run-pac-desktop.bat       # Easy startup script (Windows)
├── .env                      # Database configuration
├── frontend/                 # React frontend
│   ├── src/App.js           # Main React app
│   └── package.json         # Frontend dependencies
├── backend/                  # Python FastAPI backend
│   └── server_postgresql_fully_optimized.py
└── dist/                     # Built executables (after npm run dist)
```

## 🎉 Features

- 🖼️ **Medical Image Viewer** with DICOM support
- 👥 **Patient Management** with full records
- 📝 **Clinician Notes** on images
- 🔍 **Search and Filter** patients/images
- 🎨 **Dark/Light Mode** toggle
- 🔒 **Authentication** and user management
- ☁️ **Cloud Sync** via Supabase
- 📱 **Responsive Design** for different screen sizes

## 💡 Tips

- **First Run**: May take 2-3 minutes to install dependencies
- **Updates**: Re-run `run-pac-desktop.bat` to get latest changes  
- **Data**: All changes sync with your web version automatically
- **Offline**: Requires internet for database access
- **Performance**: Desktop version is often faster than web version
- **Multiple Devices**: Can run on multiple computers with same data

## 📞 Support

If you encounter issues:
1. Check the console output for error messages
2. Verify all requirements are installed
3. Try restarting the application
4. Check internet connection for Supabase access

The desktop app uses the same backend and database as your web version, so all features and data remain identical!
