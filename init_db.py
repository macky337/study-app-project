#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database initialization and test script
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Windows環境での文字エンコーディング設定
if sys.platform.startswith('win'):
    import locale
    locale.setlocale(locale.LC_ALL, 'C')

from database.connection import init_database, create_tables
from utils.sample_data import create_sample_data


def main():
    """メイン実行関数"""
    print("🚀 Initializing database...")
    
    # 1. テーブル作成
    print("\n📁 Creating tables...")
    if init_database():
        print("✅ Tables created successfully!")
    else:
        print("❌ Failed to create tables")
        return
    
    # 2. サンプルデータ投入
    print("\n📝 Creating sample data...")
    try:
        create_sample_data()
        print("✅ Sample data created successfully!")
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return
    
    print("\n🎉 Database initialization completed!")
    print("Now you can run: streamlit run app.py")


if __name__ == "__main__":
    main()
