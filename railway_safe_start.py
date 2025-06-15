#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway安全起動スクリプト
エラーを詳細にログ出力し、可能な限り起動を試行
"""

import os
import sys
import subprocess
import traceback
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def safe_start():
    """安全な起動処理"""
    
    logger.info("🚀 Railway Safe Start - Study Quiz App")
    logger.info("=" * 50)
    
    # 環境変数チェック
    port = os.getenv('PORT', '8080')
    database_url = os.getenv('DATABASE_URL')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    logger.info(f"Port: {port}")
    logger.info(f"DATABASE_URL: {'✅ Set' if database_url else '❌ Not set'}")
    logger.info(f"OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
    
    # Pythonパスとワーキングディレクトリ
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path[:3]}...")  # 最初の3つのパスのみ表示
    
    # 重要なファイルの存在確認
    required_files = ['app.py', 'requirements.txt', 'Procfile']
    for file in required_files:
        if os.path.exists(file):
            logger.info(f"✅ {file}: Found")
        else:
            logger.error(f"❌ {file}: Not found")
    
    # Streamlit起動コマンド構築
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--browser.gatherUsageStats", "false",
        "--server.maxUploadSize", "50"  # 50MB
    ]
    
    logger.info(f"Streamlit command: {' '.join(cmd)}")
    
    try:
        # Streamlit起動
        logger.info("🎯 Starting Streamlit...")
        
        # プロセス起動
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # stderrをstdoutにリダイレクト
            universal_newlines=True,
            bufsize=1
        )
        
        # リアルタイムでログ出力
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Streamlitのログをそのまま出力
                print(output.strip())
                
        # プロセス終了コードをチェック
        return_code = process.poll()
        if return_code != 0:
            logger.error(f"❌ Streamlit exited with code: {return_code}")
            sys.exit(return_code)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Subprocess error: {e}")
        logger.error(f"Command: {' '.join(e.cmd)}")
        logger.error(f"Return code: {e.returncode}")
        if e.output:
            logger.error(f"Output: {e.output}")
        sys.exit(1)
        
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        logger.error("Streamlit may not be installed properly")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    safe_start()
