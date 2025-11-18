from src.utils.rag import build_index, retrieve

count = build_index()
print("built chunks:", count)
if count > 0:
    print("sample retrieve:", retrieve("refund policy")[:1])
