import subprocess
import os

# カレントディレクトリをapp.pyがあるディレクトリに変更
os.chdir(r"c:\Users\user\Documents\GitHub\study-app-project")

# Streamlitアプリを起動
try:
    print("Streamlitアプリを起動しています...")
    result = subprocess.run(["streamlit", "run", "app.py"], 
                           capture_output=True, 
                           text=True,
                           check=True)
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"エラーが発生しました: {e}")
    print(f"標準出力: {e.stdout}")
    print(f"標準エラー: {e.stderr}")
except Exception as e:
    print(f"予期しないエラーが発生しました: {e}")

print("スクリプトの実行が完了しました。")
