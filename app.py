import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Railway läuft!"

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/test", methods=["POST"])
def test():
    data = request.json
    return {
        "message": "API funktioniert",
        "input": data
    }

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))  # wichtig!
    )