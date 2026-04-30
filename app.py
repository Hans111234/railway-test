"""
Flask backend for Rakuten Gold Advisor v4.5 API Ready.

IMPORTANT:
- Never put your OpenAI API key inside Rakuten Gold HTML/JS.
- Deploy this backend on Railway or another server, then set API_ENDPOINT in index.html.
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("ALLOWED_ORIGIN", "*")}})

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ALLOWED_COLORS = {
    "ミックス", "ABクリスタル", "クリア", "サファイア", "ブルージルコン",
    "アクアマリン", "ライトブルー", "ライトグリーン", "ライトパープル", "ピンク",
    "フクシア", "レッド", "シャンパン", "オレンジ", "ピンクAB",
    "バイオレットAB", "アクアAB", "ダークブルーAB", "フクシアAB", "レモンAB"
}
ALLOWED_SIZES = {"3mm", "4mm", "5mm"}


@app.get("/")
def health():
    return jsonify({"status": "ok", "service": "rakuten-gold-advisor"})


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
あなたは楽天市場の商品ページ用の短い接客コメントを書く日本語コピーライターです。
商品：樹脂コーティングパヴェ ラブレット。
サイズ選択肢：3mm / 4mm / 5mm。
おすすめサイズ：{size}
おすすめカラー：{"、".join(colors)}

固定ロジック：
{fixed_logic_text}

ルール：
- 日本語で自然に。
- 180文字以内。
- 色の魅力を必ず1つ入れる。
- サイズはおすすめとして軽く触れる。
- 「写真では3mmに見える」など、写真上のサイズ断定は絶対に書かない。
- 存在しないカラー、素材、機能は書かない。
- 医療的な断定やアレルギーが絶対大丈夫という表現は禁止。
- 最後に購入を強く煽りすぎない。
"""

    try:
        resp = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            input=prompt,
            max_output_tokens=180,
        )
        text = resp.output_text.strip()
        return jsonify({"text": text, "source": "openai"})
    except Exception as e:
        return jsonify({
            "text": fixed_logic_text,
            "source": "fallback",
            "error": str(e)[:120]
        }), 200


if __name__ == "__main__":
    # Railway sets PORT automatically. Locally this falls back to 5055.
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)
