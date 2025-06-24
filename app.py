"""
Railway設定問題検証用Flask
"""
print("=" * 60)
print("FLASK APP STARTING - NO STREAMLIT HERE!")
print("=" * 60)

try:
    from flask import Flask
    import os
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        port_vars = {k: v for k, v in os.environ.items() if 'PORT' in k.upper()}
        
        return f'''
        <html>
        <head><title>Railway Configuration Problem Detected</title></head>
        <body style="font-family: Arial; padding: 30px;">
            <h1 style="color: red;">🚨 Railway Configuration Issue Detected</h1>
            
            <h2>Problem:</h2>
            <p>Railway is executing "streamlit run app.py" despite:</p>
            <ul>
                <li>✅ Dockerfile specifies "python app.py"</li>
                <li>✅ requirements.txt has NO streamlit</li>
                <li>✅ app.py is pure Flask code</li>
                <li>❌ Railway ignores all of the above</li>
            </ul>
            
            <h2>Solution:</h2>
            <p><strong>You MUST fix Railway project settings:</strong></p>
            <ol>
                <li>Go to Railway Dashboard → General</li>
                <li>Find "Start Command" setting</li>
                <li>Change from "streamlit run app.py" to "python app.py"</li>
                <li>Or leave it blank to use Dockerfile CMD</li>
            </ol>
            
            <h2>Environment Debug:</h2>
            <pre style="background: #f5f5f5; padding: 10px;">
PORT variables: {port_vars}
Current PORT: {os.environ.get('PORT', 'Not set')}
            </pre>
            
            <h2>If you see this page:</h2>
            <p style="color: green; font-weight: bold;">✅ The fix worked! Railway is now running Flask correctly.</p>
        </body>
        </html>
        '''
    
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 8000))
        print(f"Flask starting on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
        
except Exception as e:
    print(f"Flask error: {e}")
    import traceback
    traceback.print_exc()
