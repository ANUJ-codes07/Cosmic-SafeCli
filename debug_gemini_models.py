
import os
import json
import urllib.request
import urllib.error

# Use the key from .env or hardcoded fallback
DEFAULT_GEMINI_KEY = None  # removed embedded API key for security
api_key = os.environ.get('GEMINI_API_KEY') or DEFAULT_GEMINI_KEY

def list_models():
    print(f"Checking models for key: {api_key[:10]}...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("Successfully retrieved models:")
            for model in data.get('models', []):
                print(f"- {model['name']}")
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    print(f"  (Supports generateContent)")
    except urllib.error.HTTPError as e:
        print(f"Error listing models: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
