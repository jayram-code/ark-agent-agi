"""
Simple mock shipping tracker API (Flask).
Run in a **separate terminal** before running the pipeline to simulate an OpenAPI tool.
"""

from flask import Flask, request, jsonify
import random, time

app = Flask(__name__)

@app.route("/track", methods=["GET"])
def track():
    order_id = request.args.get("order_id", "unknown")
    # simulate some random statuses
    statuses = ["in_transit","delivered","pending","lost","delayed"]
    status = random.choice(statuses)
    # simple deterministic-ish response for reproducibility
    return jsonify({
        "order_id": order_id,
        "status": status,
        "estimated_delivery_days": random.randint(0, 7),
        "last_update": time.time()
    })

if __name__ == "__main__":
    app.run(port=8082)
