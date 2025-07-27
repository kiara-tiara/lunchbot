import openai
import requests
import os
import re
from config import GOOGLE_PLACES_API_KEY
from app.sheet_client import search_lunch_records  # スプレッドシート検索関数


def get_place_photo(shop_name):
    """新しい Places API (v1) を使って写真URLを取得する"""
    search_url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.photos,places.displayName",  # 必要なフィールド
    }
    data = {
        "textQuery": shop_name + " 日本橋",
        "maxResultCount": 1,
        "languageCode": "ja",
    }

    res = requests.post(search_url, headers=headers, json=data).json()

    if "places" in res and len(res["places"]) > 0:
        place = res["places"][0]
        photos = place.get("photos", [])
        if photos:
            photo_name = photos[0][
                "name"
            ]  # 例: places/ChIJN1t_tDeuEmsRUsoyG83frY4/photos/photoRef
            # 写真を取得するURL
            photo_url = f"https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=400&key={GOOGLE_PLACES_API_KEY}"
            return photo_url

    return None


def parse_gpt_response(text):
    """
    GPTの回答テキストから、店名・所要時間・メニュー・価格・リンクをパース
    """
    suggestions = []
    blocks = re.split(r"\n- ", text)  # 「- 」で分割（GPTの箇条書きを想定）

    for block in blocks:
        shop = time = menu = price = link = ""
        for line in block.splitlines():
            if "店名" in line:
                shop = line.split("：")[-1].strip()
            elif "所要時間" in line:
                time = line.split("：")[-1].strip()
            elif "おすすめ" in line or "メニュー" in line:
                menu = line.split("：")[-1].strip()
            elif "値段" in line or "価格" in line:
                price = line.split("：")[-1].strip()
            elif "http" in line:
                link = line.strip()

        if shop:
            suggestions.append(
                {
                    "shop": shop,
                    "time": time,
                    "menu": menu,
                    "price": price,
                    "link": link,
                    "photo_url": get_place_photo(shop),
                }
            )

    return suggestions


def generate_lunch_suggestions(user_message):
    """
    スプレッドシートの履歴を検索し、見つかればそれを返す。
    なければ GPT で3件のランチ提案を取得。
    """
    matched = search_lunch_records(user_message)

    if matched:
        # スプレッドシート結果をHTMLカード用に整形
        suggestions = []
        for rec in matched:
            suggestions.append(
                {
                    "shop": rec["shop"],
                    "time": rec.get("time", "（過去記録）"),
                    "menu": rec["menu"],
                    "price": rec["price"],
                    "link": "",
                    "photo_url": get_place_photo(rec["shop"]),
                }
            )
        return {"suggestions": suggestions}

    # GPT 提案
    prompt = f"""
    ユーザーの希望：「{user_message}」
    以下の条件を守っておすすめのランチを**必ず3件**提案してください。

    - 東京都日本橋ダイヤビルディング（東京都中央区日本橋1-19-1）から徒歩20分程度以内で着くお店にしてください。
    - 存在しない店名を作らないでください。
    - Googleマップや食べログに実在するお店のみを提案してください。

    各お店について必ず次の情報を含めてください：
    - 店名（Googleマップや食べログに記載されている店舗名を引用する）
    - 東京都日本橋ダイヤビルディング（東京都中央区日本橋1-19-1）からの所要時間
    - おすすめメニュー
    - おすすめメニューの値段（例：1200円）
    - 情報源リンク（Googleマップや食べログなど）
    - リンクは Markdown を禁止。URL をそのまま出力（例: https://...）だけ

    出力は、以下の形式を**厳密に守って3件分**記載してください：

    1.
    - 店名：〇〇
    所要時間：約〇〇分
    おすすめメニュー：〇〇
    値段：〇〇円
    URL

    2.
    - 店名：〇〇
    所要時間：約〇〇分
    おすすめメニュー：〇〇
    値段：〇〇円
    URL

    3.
    - 店名：〇〇
    所要時間：約〇〇分
    おすすめメニュー：〇〇
    値段：〇〇円
    URL
    """

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "あなたは日本橋周辺のランチに詳しいグルメアドバイザーです。",
            },
            {"role": "user", "content": prompt},
        ],
    )

    answer = res.choices[0].message.content
    suggestions = parse_gpt_response(answer)
    return {"suggestions": suggestions}
