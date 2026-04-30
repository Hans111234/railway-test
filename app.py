import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("ALLOWED_ORIGIN", "*")}})

ALLOWED_COLORS = {
    "ミックス", "ABクリスタル", "クリア", "サファイア", "ブルージルコン",
    "アクアマリン", "ライトブルー", "ライトグリーン", "ライトパープル", "ピンク",
    "フクシア", "レッド", "シャンパン", "オレンジ", "ピンクAB",
    "バイオレットAB", "アクアAB", "ダークブルーAB", "フクシアAB", "レモンAB"
}

ALLOWED_SIZES = {"3mm", "4mm", "5mm"}


@app.get("/")
def home():
    return jsonify({"status": "ok"})


@app.get("/health")
def health_check():
    return jsonify({"status": "ok"})


@app.post("/api/advisor")
def advisor():
    data = request.get_json(force=True) or {}

    size = data.get("size", "4mm")
    colors = data.get("colors", [])
    fixed_logic_text = data.get("fixed_logic_text", "")

    if size not in ALLOWED_SIZES:
        size = "4mm"

    colors = [c for c in colors if c in ALLOWED_COLORS]
    if not colors:
        colors = ["クリア", "ABクリスタル"]

    prompt = f"""
商品：樹脂コーティングパヴェ ラブレット。
おすすめサイズ：{size}
おすすめカラー：{"、".join(colors)}

固定ロジック：
{fixed_logic_text}

180文字以内で自然な日本語の商品説明を書いてください。
""".strip()

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("API key missing")

        client = OpenAI(api_key=api_key)

        resp = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            input=prompt,
            max_output_tokens=180,
        )

        return jsonify({
            "text": resp.output_text.strip(),
            "source": "openai"
        })

    except Exception as e:
        return jsonify({
            "text": fixed_logic_text,
            "source": "fallback",
            "error": str(e)[:100]
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)
