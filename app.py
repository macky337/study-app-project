"""
Railway緊急対策: app.py
Streamlit実行要求をFlaskにリダイレクト
"""
import os
import sys

print("=" * 80)
print("RAILWAY EMERGENCY BYPASS: app.py")
print("Arguments:", sys.argv)
print("=" * 80)

# Flaskを起動
def run_flask():
    try:
        from flask import Flask
        
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return '''
            <html>
            <head><title>Study Quiz App - Railway Success!</title></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1>� Railway Deployment Success!</h1>
                <h2>Study Quiz App is Running</h2>
                <p>Framework: Flask (Streamlit bypass)</p>
                <p>Port: ''' + str(os.environ.get('PORT', '8000')) + '''</p>
                <p>Status: <strong style="color: green;">Active</strong></p>
                
                <h3>Environment Debug:</h3>
                <pre style="text-align: left; background: #f5f5f5; padding: 20px;">
PORT variables:
''' + '\n'.join([f"{k}={v}" for k, v in os.environ.items() if 'PORT' in k.upper()]) + '''

All environment variables:
''' + '\n'.join([f"{k}={v[:50]}..." if len(v) > 50 else f"{k}={v}" for k, v in sorted(os.environ.items())]) + '''
                </pre>
                
                <h3>Next Steps:</h3>
                <p>This confirms Railway deployment works. Now fix Streamlit version.</p>
            </body>
            </html>
            '''
        
        port = int(os.environ.get('PORT', 8000))
        print(f"Starting Flask on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        print(f"Flask startup error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_flask()
