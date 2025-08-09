#!/usr/bin/env python3
"""
BUAS System Comprehensive Health Check
This script verifies all components are working correctly
"""

import os
import sys
import sqlite3
import requests
import json
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database connectivity and structure"""
    print("🔍 Testing Database...")
    try:
        # Test SQLite database
        db_path = "uploads.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if upload table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='upload';")
            table_exists = cursor.fetchone()
            
            if table_exists:
                print("✅ Database table 'upload' exists")
                
                # Check table structure
                cursor.execute("PRAGMA table_info(upload);")
                columns = cursor.fetchall()
                expected_columns = ['id', 'device_id', 'filename', 'metadata_file', 'start_time', 'end_time', 'latitude', 'longitude', 'timestamp']
                actual_columns = [col[1] for col in columns]
                
                missing_columns = set(expected_columns) - set(actual_columns)
                if missing_columns:
                    print(f"⚠️  Missing columns: {missing_columns}")
                else:
                    print("✅ All required columns present")
            else:
                print("⚠️  Upload table does not exist")
            
            conn.close()
        else:
            print("ℹ️  Database file doesn't exist yet (will be created on first run)")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_flask_imports():
    """Test if all Flask components can be imported"""
    print("🔍 Testing Flask Imports...")
    try:
        from app import create_app
        from app.models import Upload, db
        from app.routes import routes
        print("✅ All Flask components import successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Flask import test failed: {e}")
        return False

def test_flask_app_creation():
    """Test Flask app creation"""
    print("🔍 Testing Flask App Creation...")
    try:
        from app import create_app
        app = create_app()
        
        # Test basic configuration
        assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///uploads.db'
        assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] == False
        assert app.config['MAX_CONTENT_LENGTH'] == 100 * 1024 * 1024
        
        print("✅ Flask app creates successfully with correct config")
        return True
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False

def test_cors_configuration():
    """Test CORS configuration"""
    print("🔍 Testing CORS Configuration...")
    try:
        from app import create_app
        app = create_app()
        
        # Check if CORS is configured
        with app.test_client() as client:
            # Test OPTIONS request (preflight)
            response = client.options('/api/dashboard-data')
            
            # Should return 200 for OPTIONS
            if response.status_code == 200:
                print("✅ CORS preflight handling works")
                return True
            else:
                print(f"⚠️  OPTIONS request returned {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_routes():
    """Test all API routes"""
    print("🔍 Testing API Routes...")
    try:
        from app import create_app
        app = create_app()
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/health')
            if response.status_code == 200:
                print("✅ Health endpoint works")
            else:
                print(f"⚠️  Health endpoint returned {response.status_code}")
            
            # Test dashboard data endpoint
            response = client.get('/api/dashboard-data')
            if response.status_code == 200:
                data = json.loads(response.data)
                required_keys = ['total_users', 'users', 'stats', 'connection_status']
                if all(key in data for key in required_keys):
                    print("✅ Dashboard data endpoint works with correct structure")
                else:
                    print(f"⚠️  Dashboard data missing keys: {set(required_keys) - set(data.keys())}")
            else:
                print(f"⚠️  Dashboard data endpoint returned {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Routes test failed: {e}")
        return False

def test_frontend_files():
    """Test frontend file structure"""
    print("🔍 Testing Frontend Files...")
    
    frontend_path = "frontend"
    if not os.path.exists(frontend_path):
        print("❌ Frontend directory doesn't exist")
        return False
    
    required_files = [
        "package.json",
        "src/App.js",
        "src/index.js",
        "src/services/api.js",
        "src/components/Dashboard.js",
        "src/components/UserList.js",
        "src/components/AudioPlayer.js",
        "src/components/StatusBar.js",
        "src/components/ConnectionStatus.js",
        "src/components/ErrorBoundary.js",
        "public/index.html"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(frontend_path, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing frontend files: {missing_files}")
        return False
    else:
        print("✅ All required frontend files exist")
        return True

def test_environment_files():
    """Test environment configuration files"""
    print("🔍 Testing Environment Files...")
    
    env_files = [
        "frontend/.env.local",
        "frontend/.env.example",
        "frontend/.env.production"
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ {env_file} exists")
        else:
            print(f"⚠️  {env_file} missing")
    
    return True

def main():
    """Run all tests"""
    print("🦇 BUAS System Health Check")
    print("=" * 50)
    
    tests = [
        test_flask_imports,
        test_flask_app_creation,
        test_database,
        test_cors_configuration,
        test_routes,
        test_frontend_files,
        test_environment_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your BUAS system is ready to run!")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
    
    print("\n🚀 To start the system:")
    print("1. Backend: python server.py")
    print("2. Frontend: cd frontend && npm install && npm start")

if __name__ == "__main__":
    main()
