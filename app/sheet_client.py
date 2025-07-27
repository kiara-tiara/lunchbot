import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import openai

CREDENTIALS_FILE = "credentials/service_account.json"
SHEET_NAME = "ランチのお店リスト"


def generate_keywords(menu):
    messages = [
        {
            "role": "system",
            "content": "料理名を入力されたら、それに関連する検索用のキーワードをカンマ区切りで5個以内で返してください。ユーザーの検索語として有効な単語にしてください。出力はキーワードのみ。",
        },
        {"role": "user", "content": menu},
    ]
    res = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    return res.choices[0].message.content.strip()


def get_sheet():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS が環境変数に設定されていません。")

    # デバッグ: 先頭100文字だけ表示
    print("DEBUG RAW:", creds_json[:100])

    # 改行コードを復元
    creds_json = creds_json.replace("\\n", "\n")
    creds_dict = json.loads(creds_json)

    # private_keyを確認
    print("DEBUG PRIVATE KEY:", creds_dict["private_key"][:50])

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet


def append_feedback(shop, menu, price, mood, comment):
    sheet = get_sheet()
    today = datetime.date.today().isoformat()
    keywords = generate_keywords(menu)
    sheet.append_row([today, shop, menu, price, mood, comment, keywords])


def search_lunch_records(keyword):
    """
    スプレッドシートから、キーワードにマッチするレコードを探す。
    """
    sheet = get_sheet()
    records = sheet.get_all_values()[1:]  # ヘッダー除外
    matched = []

    for row in records:
        if len(row) < 6:
            continue  # 不正行スキップ

        date, shop, menu, price, mood, comment, *rest = row
        all_text = " ".join(row).lower()

        if keyword.lower() in all_text:
            matched.append(
                {
                    "shop": shop,
                    "menu": menu,
                    "price": price,
                    "mood": mood,
                    "comment": comment,
                }
            )

    return matched
