#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unicodeエラー修正スクリプト
Windows環境での絵文字・Unicode文字エラーを修正
"""

import os
import re

def fix_unicode_in_file(file_path):
    """ファイル内のUnicode文字を修正"""
    
    # Unicode文字の置換マップ
    replacements = {
        '✅': 'OK:',
        '❌': 'ERROR:',
        '⚠️': 'WARN:',
        '🔍': 'INFO:',
        '🔒': 'PRIVACY:',
        '💾': 'SAVED:',
        '📊': 'STATS:',
        '📋': 'LIST:',
        '💡': 'TIP:',
        '🔧': 'FIX:',
        '⚡': 'FAST:',
        '🚀': 'START:',
        '📖': 'READ:',
        '🎯': 'TARGET:',
        '✨': 'NEW:',
        '🔥': 'HOT:',
        '💯': 'FULL:',
        '📈': 'UP:',
        '📉': 'DOWN:',
        '🎉': 'SUCCESS:',
        '🤖': 'AI:',
        '💡': 'IDEA:',
        '🏆': 'WIN:',
        '⭐': 'STAR:',
        '🎭': 'MASK:',
        '🌟': 'BRIGHT:',
        '🚨': 'ALERT:',
    }
    
    try:
        # ファイルを読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # バックアップを作成
        backup_path = file_path + '.bak'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"修正対象: {file_path}")
        
        # 置換実行
        modified = False
        for unicode_char, replacement in replacements.items():
            if unicode_char in content:
                content = content.replace(unicode_char, replacement)
                modified = True
                print(f"  置換: '{unicode_char}' -> '{replacement}'")
        
        # 修正されたファイルを保存
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 修正完了: {file_path}")
        else:
            print(f"- 修正不要: {file_path}")
            # バックアップファイルを削除
            os.remove(backup_path)
        
        return modified
        
    except Exception as e:
        print(f"エラー: {file_path} - {e}")
        return False

def main():
    """メイン処理"""
    
    print("Unicode エラー修正スクリプト")
    print("=" * 50)
    
    # 修正対象ファイル
    target_files = [
        'services/enhanced_openai_service.py',
        'services/past_question_extractor.py',
    ]
    
    modified_count = 0
    
    for file_path in target_files:
        if os.path.exists(file_path):
            if fix_unicode_in_file(file_path):
                modified_count += 1
        else:
            print(f"ファイルが見つかりません: {file_path}")
    
    print("\n" + "=" * 50)
    print(f"修正完了: {modified_count}個のファイルを修正")
    print("バックアップファイル (.bak) が作成されました")

if __name__ == "__main__":
    main()
