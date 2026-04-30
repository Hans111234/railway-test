import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Railway läuft!"

@app.route("/health")
def health():
    return {"status": "ok"}

# 👉 Produkt / Model API
@app.route("/advisor", methods=["POST"])
def advisor():
    data = request.json
    
    return {
        "status": "ok",
        "input": data,
        "recommendation": "Model B geeignet",
        "next_step": "generate image"
    }

# 👉 Image Trigger (später AI)
@app.route("/generate-image", methods=["POST"])
def generate_image():
    data = request.json
    
    return {
        "status": "ok",
        "message": "Image generation started",
        "input": data
    }

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )