REQUIRED_FIELDS = [
    "id",
    "session_id",
    "sender",
    "receiver",
    "type",
    "timestamp",
    "payload"
]

def validate_message(msg):
    for key in REQUIRED_FIELDS:
        if key not in msg:
            raise ValueError(f"Missing required field: {key}")
    return True
