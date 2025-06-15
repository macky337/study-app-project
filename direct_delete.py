import os

# test_*ファイルのリスト
test_files = [
    "test_extraction.py",
    "test_fallback.py", 
    "test_fix.py",
    "test_imports.py",
    "test_improved_extraction.py",
    "test_openai.py",
    "test_openai_simple.py",
    "test_pdf_full.py",
    "test_pdf_function.py",
    "test_pdf_processor.py",
    "test_privacy.py",
    "test_streamlit.py",
    "test_streamlit_startup.py"
]

for file in test_files:
    try:
        if os.path.exists(file):
            os.remove(file)
            print(f"Deleted: {file}")
    except Exception as e:
        print(f"Error deleting {file}: {e}")

print("Deletion complete")
