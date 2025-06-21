import os
import shutil

# ファイルパス
current_dir = r"c:\Users\user\Documents\GitHub\study-app-project"
app_py_path = os.path.join(current_dir, "app.py")
fixed_backup_path = os.path.join(current_dir, "app.py.true_final_fix.backup")
new_backup_path = os.path.join(current_dir, "app.py.before_fix_" + 
                             "".join([c for c in str(os.path.getmtime(app_py_path)) if c.isdigit()])[:12] + ".backup")

# 現在のapp.pyをバックアップ
shutil.copy2(app_py_path, new_backup_path)
print(f"現在のapp.pyを{new_backup_path}にバックアップしました。")

# 修正済みのバックアップを現在のapp.pyにコピー
shutil.copy2(fixed_backup_path, app_py_path)
print(f"修正済みのバックアップ{fixed_backup_path}をapp.pyに適用しました。")

print("修正が完了しました！")
