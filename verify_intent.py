import os
import sys
import time
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from utils.gemini_utils import classify_intent

load_dotenv()

text = "Where is my order? I placed it 2 weeks ago and tracking hasn't updated."
print(f"Testing Intent Classification for: '{text}'")

try:
    result = classify_intent(text)
    print("\nResult:")
    print(result)
    
    if result.get("intent") == "shipping_inquiry":
        print("\nSUCCESS: Correctly classified as shipping_inquiry")
    else:
        print(f"\nFAILURE: Classified as {result.get('intent')}")

except Exception as e:
    print(f"\nERROR: {e}")
