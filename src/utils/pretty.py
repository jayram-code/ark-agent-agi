import json
def pretty(msg):
    try:
        print(json.dumps(msg, indent=2, ensure_ascii=False))
    except Exception:
        print(msg)
