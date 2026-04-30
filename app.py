import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("ALLOWED_ORIGIN", "*")}})

# Truth-locked product data: the AI may only use these known options.
ALLOWED_COLORS = {
    "ミックス", "ABクリスタル", "クリア", "サファイア", "ブルージルコン",
    "アクアマリン", "ライトブルー", "ライトグリーン", "ライトパープル", "ピンク",
    "フクシア", "レッド", "シャンパン", "オレンジ", "ピンクAB",
    "バイオレットAB", "アクアAB", "ダークブルーAB", "フクシアAB", "レモンAB"
}

ALLOWED_SIZES = {"3mm", "4mm", "5mm"}

SCENE_LABELS = {
    "office": "仕事や学校でも使いやすい清潔感のあるシーン",
    "daily": "毎日のコーデに自然に合わせやすい普段使い",
    "date": "やわらかく可愛い印象を出したいシーン",
    "event": "お出かけやイベントで少し華やかに見せたいシーン",
}

MOOD_LABELS = {
    "subtle": "控えめで上品",
    "cute": "かわいい印象",
    "adult": "落ち着いた大人っぽい印象",
    "cool": "すっきりしたクールな印象",
    "sparkle": "華やかで輝きのある印象",
    "fresh": "明るく爽やかな印象",
}

COLOR_REASON = {
    "クリア": "透明感があり、清潔感のある印象に見せやすいカラーです。",
    "ABクリスタル": "光の角度で表情が変わり、さりげないきらめきを楽しめます。",
    "ピンク": "顔まわりを明るく見せ、やわらかく可愛い雰囲気に合います。",
    "ライトパープル": "甘すぎず、やさしい印象に合わせやすいカラーです。",
    "フクシア": "可愛さの中に少し華やかさを足したい時に向いています。",
    "シャンパン": "肌なじみがよく、落ち着いた上品な雰囲気に合わせやすいカラーです。",
    "ミックス": "複数の色味が入るため、コーデの小さなアクセントになります。",
    "サファイア": "深みのあるブルーで、すっきりとクールな印象に合います。",
    "ブルージルコン": "明るめのブルーで、爽やかさと存在感を出しやすいカラーです。",
    "ライトブルー": "軽やかで清潔感のある印象に合わせやすいカラーです。",
    "アクアマリン": "爽やかで明るい印象を作りやすいカラーです。",
    "ライトグリーン": "やさしく明るい雰囲気に合わせやすいカラーです。",
    "ピンクAB": "可愛い印象に、光で変わる華やかさを加えられます。",
    "アクアAB": "爽やかさときらめきを両方楽しみやすいカラーです。",
    "レモンAB": "明るく軽やかな印象を出したい時に向いています。",
    "フクシアAB": "華やかで可愛い印象をしっかり出しやすいカラーです。",
    "バイオレットAB": "落ち着きと華やかさを両方楽しみやすいカラーです。",
    "ダークブルーAB": "大人っぽく、光で変わる表情も楽しめるカラーです。",
    "オレンジ": "明るく元気な印象に合わせやすいカラーです。",
    "レッド": "小さくても印象を残しやすいアクセントカラーです。",
}

SIZE_REASON = {
    "3mm": "3mmは控えめに見せたい時に選びやすいサイズ感です。",
    "4mm": "4mmは小さすぎず大きすぎない、迷った時に選びやすいバランス型です。",
    "5mm": "5mmはカラーの印象をしっかり楽しみたい時に向いています。",
}

BANNED_WORDS = [
    "アレルギーでも安心", "絶対", "必ず", "医療", "治療", "安全", "かぶれない",
    "金属アレルギー対応", "アレルギー対応", "医療用", "永久", "完全"
]


def normalize_size(value):
    if value not in ALLOWED_SIZES:
        return "4mm"
    return value


def normalize_colors(values):
    if not isinstance(values, list):
        values = []
    colors = [str(c).strip() for c in values if str(c).strip() in ALLOWED_COLORS]
    if not colors:
        colors = ["クリア", "ABクリスタル"]
    return colors[:4]


def fallback_text(scene, mood, size, colors):
    scene_text = SCENE_LABELS.get(scene, SCENE_LABELS["daily"])
    mood_text = MOOD_LABELS.get(mood, MOOD_LABELS["subtle"])
    color_text = " ".join(COLOR_REASON.get(c, "") for c in colors[:2]).strip()
    size_text = SIZE_REASON.get(size, SIZE_REASON["4mm"])
    return f"{scene_text}に合わせやすい、{mood_text}なスタイルです。{color_text} {size_text}迷ったらこの組み合わせから選ぶと、毎日のコーデにも取り入れやすい印象です。"


def clean_text(text):
    text = str(text or "").strip()
    text = text.replace("【", "").replace("】", "")
    text = text.replace("AI", "").replace("人工知能", "")
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" 。", "。").replace("、。", "。")
    return text.strip()


def validate_output(text, colors):
    if not text:
        return False

    # block risky claims
    for word in BANNED_WORDS:
        if word in text:
            return False

    # block colors that are not in allowed set, if they look like known product colors
    for c in ALLOWED_COLORS:
        if c in text and c not in colors:
            return False

    # keep text reasonably short for Rakuten mobile
    if len(text) > 210:
        return False

    return True


@app.get("/")
def home():
    return jsonify({"status": "ok", "service": "rakuten-advisor-conversion-v2"})


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/advisor")
def advisor():
    data = request.get_json(force=True) or {}

    scene = str(data.get("scene", "daily")).strip()
    mood = str(data.get("mood", "subtle")).strip()
    size = normalize_size(str(data.get("size", "4mm")).strip())
    colors = normalize_colors(data.get("colors", []))
    color_label = str(data.get("color_label", "")).strip()
    fixed_logic_text = str(data.get("fixed_logic_text", "")).strip()

    scene_text = SCENE_LABELS.get(scene, SCENE_LABELS["daily"])
    mood_text = MOOD_LABELS.get(mood, MOOD_LABELS["subtle"])
    size_text = SIZE_REASON.get(size, SIZE_REASON["4mm"])
    color_truth = "\n".join([f"- {c}: {COLOR_REASON.get(c, '')}" for c in colors])

    local_fallback = fixed_logic_text or fallback_text(scene, mood, size, colors)

    prompt = f"""
あなたは楽天市場の商品ページ用の販売接客コピーライターです。
目的は、ユーザーが迷わずカラーとサイズを選べるようにすることです。

商品：
樹脂コーティングパヴェ ラブレット

選択条件：
- シーン: {scene_text}
- 印象: {mood_text}
- サイズ: {size}
- サイズ説明: {size_text}
- カラー: {"、".join(colors)}
- カラー分類: {color_label}

使ってよいカラー説明：
{color_truth}

厳守ルール：
- 日本語のみ
- 120〜170文字
- 文章のみ。JSON、見出し、記号装飾は禁止
- 存在しないカラー、素材、機能を書かない
- 医療、安全、アレルギーに関する断定は禁止
- 「絶対」「必ず」「完全」などの断定は禁止
- 過度な煽りは禁止
- 最後は強い購入催促ではなく、自然な選びやすさで締める
- 「迷ったら」「選びやすい」「取り入れやすい」のうち1つを自然に入れる
- 色の魅力を1つ以上入れる
- サイズ感に軽く触れる

出力：
文章のみ
""".strip()

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY missing")

        client = OpenAI(api_key=api_key)
        resp = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            input=prompt,
            max_output_tokens=220,
        )

        text = clean_text(resp.output_text)

        if not validate_output(text, colors):
            raise Exception("output validation failed")

        return jsonify({
            "text": text,
            "source": "openai",
            "version": "conversion-v2"
        })

    except Exception as e:
        return jsonify({
            "text": clean_text(local_fallback),
            "source": "fallback",
            "version": "conversion-v2",
            "error": str(e)[:160]
        })


@app.post("/api/generate-image")
def generate_image():
    data = request.get_json(force=True) or {}
    return jsonify({
        "status": "ok",
        "message": "Image generation placeholder",
        "input": data
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)
