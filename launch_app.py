#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Launch Check - アプリケーション起動前チェック
"""

import os
import subprocess
import sys

def check_environment():
    """環境の基本チェック"""
    print("🔍 Environment Check")
    print("-" * 30)
    
    # Python version
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # .env file
    env_exists = os.path.exists('.env')
    print(f"⚙️  .env file: {'✅ Found' if env_exists else '❌ Missing'}")
    
    if env_exists:
        with open('.env', 'r') as f:
            content = f.read()
            has_openai = 'OPENAI_API_KEY=' in content
            has_db = 'DATABASE_URL=' in content
            print(f"   📋 OPENAI_API_KEY: {'✅' if has_openai else '❌'}")
            print(f"   📋 DATABASE_URL: {'✅' if has_db else '❌'}")
    
    # Requirements file
    req_exists = os.path.exists('requirements.txt')
    print(f"📦 requirements.txt: {'✅ Found' if req_exists else '❌ Missing'}")
    
    # Key files
    key_files = ['app.py', 'database/', 'services/', 'models/']
    print("📂 Key files:")
    for file in key_files:
        exists = os.path.exists(file)
        print(f"   {file}: {'✅' if exists else '❌'}")
    
    return env_exists and req_exists

def install_requirements():
    """必要なパッケージのインストール"""
    print("\n📥 Installing Requirements")
    print("-" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Requirements installed successfully")
            return True
        else:
            print("❌ Failed to install requirements:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Installation timeout (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def launch_app():
    """アプリケーションの起動"""
    print("\n🚀 Launching Application")
    print("-" * 30)
    print("Starting Streamlit app...")
    print("👀 Your browser should open automatically")
    print("🌐 If not, go to: http://localhost:8501")
    print("\n🛑 Press Ctrl+C to stop the app")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])
    except KeyboardInterrupt:
        print("\n\n✋ App stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start app: {e}")

def main():
    print("🎯 Study Quiz App - Launch Check")
    print("=" * 50)
    
    # Environment check
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Package installation failed. Please check the errors above.")
        return
    
    print("\n✅ All checks passed!")
    print("\n" + "=" * 50)
    
    # Launch app
    launch_app()

if __name__ == "__main__":
    main()
