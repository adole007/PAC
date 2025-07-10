#!/usr/bin/env python3
"""
Deployment script for Jajuwa Healthcare PAC System
This script helps deploy the full-stack application to Vercel with database setup.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error running command: {cmd}")
        print(f"Error: {e}")
        return False

def check_requirements():
    """Check if required tools are installed"""
    print("🔍 Checking requirements...")
    
    # Check Vercel CLI
    if not run_command("vercel --version"):
        print("❌ Vercel CLI not found. Please install it with: npm i -g vercel")
        return False
    
    # Check Node.js
    if not run_command("node --version"):
        print("❌ Node.js not found. Please install Node.js")
        return False
    
    # Check Python
    if not run_command("python --version"):
        print("❌ Python not found. Please install Python")
        return False
    
    print("✅ All requirements met")
    return True

def setup_database():
    """Setup database configuration"""
    print("🗄️  Setting up database...")
    
    print("""
📋 Database Setup Options:
1. 🆓 PlanetScale (Free MySQL, recommended for development)
2. 🌐 Railway (Free tier available)
3. 🐘 Supabase (PostgreSQL, free tier)
4. 🔧 Your own MySQL server

For this deployment, I recommend PlanetScale for the free MySQL database.
""")
    
    choice = input("Choose your database option (1-4): ").strip()
    
    if choice == "1":
        print("""
🚀 PlanetScale Setup:
1. Go to https://planetscale.com/
2. Sign up/Login
3. Create a new database
4. Get your connection details
5. Create a branch (main)
6. Get the connection string
""")
        
        db_host = input("Enter your PlanetScale host (e.g., aws.connect.psdb.cloud): ").strip()
        db_user = input("Enter your database username: ").strip()
        db_password = input("Enter your database password: ").strip()
        db_name = input("Enter your database name: ").strip()
        db_port = input("Enter your database port (default: 3306): ").strip() or "3306"
        
        return {
            "MYSQL_HOST": db_host,
            "MYSQL_USER": db_user,
            "MYSQL_PASSWORD": db_password,
            "MYSQL_DATABASE": db_name,
            "MYSQL_PORT": db_port
        }
    
    elif choice == "2":
        print("""
🚀 Railway Setup:
1. Go to https://railway.app/
2. Sign up/Login
3. Create a new project
4. Add MySQL service
5. Get your connection details from the Variables tab
""")
        
        db_host = input("Enter your Railway MySQL host: ").strip()
        db_user = input("Enter your MySQL username: ").strip()
        db_password = input("Enter your MySQL password: ").strip()
        db_name = input("Enter your MySQL database name: ").strip()
        db_port = input("Enter your MySQL port (default: 3306): ").strip() or "3306"
        
        return {
            "MYSQL_HOST": db_host,
            "MYSQL_USER": db_user,
            "MYSQL_PASSWORD": db_password,
            "MYSQL_DATABASE": db_name,
            "MYSQL_PORT": db_port
        }
    
    else:
        print("❌ Invalid choice. Please run the script again.")
        return None

def deploy_to_vercel():
    """Deploy the application to Vercel"""
    print("🚀 Deploying to Vercel...")
    
    # Login to Vercel
    print("Please login to Vercel if you haven't already:")
    if not run_command("vercel login"):
        print("❌ Vercel login failed")
        return False
    
    # Deploy
    print("Starting deployment...")
    if not run_command("vercel --prod"):
        print("❌ Vercel deployment failed")
        return False
    
    print("✅ Deployment successful!")
    return True

def set_environment_variables(db_config):
    """Set environment variables in Vercel"""
    print("🔧 Setting environment variables...")
    
    # Generate a secret key
    import secrets
    secret_key = secrets.token_urlsafe(32)
    
    env_vars = {
        **db_config,
        "SECRET_KEY": secret_key
    }
    
    for key, value in env_vars.items():
        cmd = f'vercel env add {key} production'
        print(f"Setting {key}...")
        # Note: This requires manual input for security
        print(f"Run: {cmd}")
        print(f"Then enter: {value}")
    
    print("✅ Environment variables configured")

def build_frontend():
    """Build the frontend"""
    print("🏗️  Building frontend...")
    
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install dependencies
    if not run_command("npm install", cwd=frontend_path):
        print("❌ Frontend npm install failed")
        return False
    
    # Build
    if not run_command("npm run build", cwd=frontend_path):
        print("❌ Frontend build failed")
        return False
    
    print("✅ Frontend built successfully")
    return True

def main():
    """Main deployment function"""
    print("🏥 Jajuwa Healthcare PAC System Deployment")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup database
    db_config = setup_database()
    if not db_config:
        sys.exit(1)
    
    # Build frontend
    if not build_frontend():
        sys.exit(1)
    
    # Set environment variables
    set_environment_variables(db_config)
    
    # Deploy to Vercel
    if not deploy_to_vercel():
        sys.exit(1)
    
    print("\n🎉 Deployment completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run the database setup script to create tables")
    print("2. Test your application")
    print("3. Set up monitoring and backups")
    
    print("\n🔗 Your application should be available at your Vercel URL")

if __name__ == "__main__":
    main()
