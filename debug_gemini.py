
import os
import sys
import google.generativeai as genai

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from utils.gemini_utils import classify_intent

def test():
    print(f"API Key present: {bool(os.getenv('GOOGLE_API_KEY'))}")
    try:
        # Configure explicitly to be sure
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello")
        print("Basic generation success!")
        print(response.text)
    except Exception as e:
        print(f"Basic generation failed: {e}")

    print("\nTesting classify_intent...")
    try:
        result = classify_intent("The app keeps crashing.")
        print(f"Result: {result}")
    except Exception as e:
        print(f"classify_intent failed: {e}")

if __name__ == "__main__":
    test()
