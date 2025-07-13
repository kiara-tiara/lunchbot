from flask import Flask, request, render_template
from dotenv import load_dotenv
import openai
import os

app = Flask(__name__)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=["GET", "POST"])
def chat():
    response = ""
    if request.method == "POST":
        message = request.form["message"]

        prompt = f"""ユーザーの今日のリクエスト：{message}
日本橋周辺でおすすめのランチ店を3つ紹介してください。
親しみやすいトーンで、具体的にメニュー名・お店の特徴・価格も書いてください。
参考にしたWEBサイトのリンクも添付してください。"""

        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは親しみやすいグルメアドバイザーです。"},
                {"role": "user", "content": prompt}
            ]
        )
        response = res.choices[0].message.content

    return render_template("chat.html", response=response)

# ←これがないと Flask はしゃべらない！
if __name__ == "__main__":
    app.run(debug=True)
