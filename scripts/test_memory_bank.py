from src.storage.memory_bank import get_recent, init, recall_relevant, store_interaction

print("init")
init()

print("store")
id1 = store_interaction("C100", "ticket", "Customer reported missing order #999")
id2 = store_interaction("C100", "note", "Called customer; awaiting reply")

print("recent:", get_recent("C100"))

print("recall:", recall_relevant("C100", "missing order", k=3))
