import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

ALLOWED_COLORS = {
    "ミックス","ABクリスタル","クリア","サファイア","ブルージルコン",
    "アクアマリン","ライトブルー","ライトグリーン","ライトパープル","ピンク",
    "フクシア","レッド","シャンパン","オレンジ","ピンクAB",
    "バイオレットAB","アクアAB","ダークブルーAB","フクシアAB","レモンAB"
}

ALLOWED_SIZES = {"3mm","4mm","5mm"}

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/api/advisor")
def advisor():
    data = request.get_json(force=True) or {}
    size = data.get("size","4mm")
    colors = [c for c in data.get("colors",[]) if c in ALLOWED_COLORS]
    if not colors:
        colors = ["クリア","ABクリスタル"]

    prompt = f"サイズ:{size} カラー:{','.join(colors)} 自然な商品説明を140文字以内で書いて"

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.responses.create(
            model=os.getenv("OPENAI_MODEL","gpt-5.4-mini"),
            input=prompt,
            max_output_tokens=180
        )
        return {"text":resp.output_text.strip(),"source":"openai"}
    except Exception as e:
        return {"text":"シンプルで使いやすい定番スタイルです。","source":"fallback"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)
