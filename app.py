from flask import Flask, request, render_template
import openai
import os
from app.sheet_client import append_feedback

from app.lunch_suggester import generate_lunch_suggestions

from config import OPENAI_API_KEY, SECRET_KEY

openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route("/", methods=["GET", "POST"])
def chat():
    response = None
    if request.method == "POST":
        message = request.form["message"]
        response = generate_lunch_suggestions(message)
    return render_template("chat.html", response=response)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        shop = request.form.get("shop", "").strip()
        menu = request.form.get("menu", "").strip()
        price = request.form.get("price", "").strip()
        mood = request.form.get("mood", "").strip()
        comment = request.form.get("comment", "").strip()

        if all([shop, menu, price, mood, comment]):

            append_feedback(shop, menu, price, mood, comment)
            return render_template("register.html", success=True)
        else:
            return render_template("register.html", error="すべての項目を入力してね！")

    return render_template("register.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
