"""
OpenAI接続テスト専用スクリプト
Railway環境でのネットワーク接続をデバッグ
"""

import os
import sys
import time
import socket
import requests
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def test_basic_network():
    """基本的なネットワーク接続テスト"""
    print("=== 基本ネットワーク接続テスト ===")
    
    # DNS解決テスト
    try:
        import socket
        host_ip = socket.gethostbyname("api.openai.com")
        print(f"✅ DNS解決成功: api.openai.com -> {host_ip}")
    except Exception as e:
        print(f"❌ DNS解決失敗: {e}")
        return False
    
    # TCP接続テスト
    try:
        sock = socket.create_connection(("api.openai.com", 443), timeout=10)
        sock.close()
        print("✅ TCP接続成功: api.openai.com:443")
    except Exception as e:
        print(f"❌ TCP接続失敗: {e}")
        return False
    
    # HTTPS接続テスト
    try:
        response = requests.get("https://api.openai.com", timeout=10)
        print(f"✅ HTTPS接続成功: ステータスコード {response.status_code}")
    except Exception as e:
        print(f"❌ HTTPS接続失敗: {e}")
        return False
    
    return True

def test_openai_simple():
    """シンプルなOpenAI API接続テスト"""
    print("\n=== OpenAI API接続テスト ===")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY環境変数が設定されていません")
        return False
    
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        from openai import OpenAI
        
        # クライアント作成
        client = OpenAI(
            api_key=api_key,
            timeout=30.0,
            max_retries=3
        )
        print("✅ OpenAIクライアント作成成功")
        
        # API呼び出し
        print("🤖 API呼び出し実行中...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, please respond with just 'OK'"}
            ],
            max_tokens=10,
            timeout=20
        )
        
        if response and response.choices:
            result = response.choices[0].message.content
            print(f"✅ API呼び出し成功: {result}")
            return True
        else:
            print("❌ API応答が空です")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API呼び出し失敗: {type(e).__name__}: {e}")
        import traceback
        print("詳細なエラー情報:")
        print(traceback.format_exc())
        return False

def test_railway_specific():
    """Railway固有の問題をテスト"""
    print("\n=== Railway環境テスト ===")
    
    # 環境変数確認
    env_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY", 
        "RAILWAY_ENVIRONMENT",
        "PORT"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if var == "OPENAI_API_KEY":
                print(f"✅ {var}: {value[:10]}...{value[-4:]}")
            elif var == "DATABASE_URL":
                print(f"✅ {var}: {value[:20]}...{value[-10:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未設定")
    
    # プロキシ設定確認
    proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
    proxy_found = False
    for var in proxy_vars:
        value = os.getenv(var)
        if value:
            print(f"🌐 プロキシ設定: {var}={value}")
            proxy_found = True
    
    if not proxy_found:
        print("ℹ️ プロキシ設定なし（通常は正常）")
    
    # Railway環境確認
    railway_env = os.getenv("RAILWAY_ENVIRONMENT")
    if railway_env:
        print(f"🚂 Railway環境: {railway_env}")
    else:
        print("ℹ️ ローカル環境またはRailway環境変数未設定")

def main():
    """メインテスト実行"""
    print("🔍 OpenAI接続診断ツール")
    print("=" * 50)
    
    # 段階的にテスト実行
    success_count = 0
    total_tests = 3
    
    if test_basic_network():
        success_count += 1
    
    if test_openai_simple():
        success_count += 1
    
    # Railway固有テストは常に実行（診断のみ）
    test_railway_specific()
    success_count += 1
    
    print("\n" + "=" * 50)
    print(f"テスト結果: {success_count}/{total_tests} 成功")
    
    if success_count == total_tests:
        print("✅ すべてのテストが成功しました！")
        return True
    else:
        print("❌ 一部のテストが失敗しました")
        print("\n推奨対処:")
        print("1. ネットワーク接続を確認")
        print("2. Railway環境変数を確認")
        print("3. OpenAI APIキーを確認")
        print("4. Railwayサポートに問い合わせ")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
