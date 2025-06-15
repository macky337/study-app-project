#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlitアプリ起動テスト
"""

import subprocess
import time
import sys
import os

def test_streamlit_startup():
    """Streamlitアプリの起動テスト"""
    print("🚀 Streamlitアプリ起動テスト")
    print("=" * 50)
    
    # 現在のディレクトリを確認
    current_dir = os.getcwd()
    print(f"📁 現在のディレクトリ: {current_dir}")
    
    # app.pyの存在確認
    app_path = os.path.join(current_dir, "app.py")
    if os.path.exists(app_path):
        print("✅ app.py が見つかりました")
    else:
        print("❌ app.py が見つかりません")
        return False
    
    # config.tomlの確認
    config_path = os.path.join(current_dir, ".streamlit", "config.toml")
    if os.path.exists(config_path):
        print("✅ .streamlit/config.toml が見つかりました")
        with open(config_path, 'r') as f:
            content = f.read()
            if 'localhost' in content:
                print("✅ localhost設定が確認されました")
            else:
                print("⚠️  localhost設定が見つかりません")
    else:
        print("❌ .streamlit/config.toml が見つかりません")
    
    print("\n🌐 正しいアクセスURL:")
    print("   http://localhost:8501")
    print("\n💡 起動コマンド:")
    print("   streamlit run app.py")
    
    return True

if __name__ == "__main__":
    test_streamlit_startup()
