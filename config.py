# config.py
from dotenv import load_dotenv
import os

# .envの読み込み
load_dotenv()

# 各種APIキーや設定値
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "dev")
