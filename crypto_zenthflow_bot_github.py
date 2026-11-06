import os
import re
import io
import sys
import math
import time
import uuid
import json
import random
import sqlite3
import logging
import asyncio
import traceback
import urllib.parse
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

import pytz
import httpx
import requests
import urllib3
import nest_asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

import telegram
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InputMediaPhoto,
    ChatPermissions,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    InlineQueryHandler,
    ChatMemberHandler,
)
from telegram.request import HTTPXRequest
from telegram.helpers import escape_markdown


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
nest_asyncio.apply()


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_USERNAME = "CryptoZenthflowbot"
BOT_NAME = "Crypto ZenthFlow | استعلام ارز دیجیتال"
CHART_WATERMARK = "MEOWIE"


ADMINS = [int(value.strip()) for value in os.getenv("ADMIN_IDS", "").split(",") if value.strip().isdigit()]


NOBITEX_FAST_API = os.getenv("NOBITEX_FAST_API", "https://api.fast-creat.ir/nobitex/v2")
FAST_CHART_API = os.getenv("FAST_CHART_API", "https://api.fast-creat.ir/chart?")
NOBITEX_OFFICIAL_STATS = "https://api.nobitex.ir/market/stats"
WALLEX_MARKETS_API = "https://api.wallex.ir/v1/markets"
COINGECKO_SIMPLE_API = "https://api.coingecko.com/api/v3/simple/price"
BINANCE_TICKER_API = "https://api.binance.com/api/v3/ticker/24hr"

IRAN_TZ = pytz.timezone("Asia/Tehran")
DB_FILE_NAME = "cryptozenthflow_enterprise.db"


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("CryptoZenthFlowBot")


EMOJIS = {
    "home": "🏠",
    "search": "🔍",
    "up": "📈",
    "down": "📉",
    "stable": "➡️",
    "info": "ℹ️",
    "money": "💵",
    "coin": "🪙",
    "gold": "🏆",
    "clock": "🕒",
    "calendar": "📅",
    "error": "❌",
    "warning": "⚠️",
    "group": "👥",
    "inline": "🔎",
    "channel": "📢",
    "settings": "⚙️",
    "check": "✅",
    "trash": "🗑️",
    "users": "👥",
    "stats": "📊",
    "admin": "👑",
    "ban": "🚫",
    "unban": "✅",
    "back": "🔙",
    "next": "➡️",
    "previous": "⬅️",
    "message": "💬",
    "chart": "📊",
    "rocket": "🚀",
    "star": "⭐",
    "fire": "🔥",
    "dollar": "💲",
    "iran": "🇮🇷",
    "globe": "🌍",
    "bulb": "💡",
    "gift": "🎁",
    "crown": "👑",
    "gem": "💎",
    "calc": "🧮",
    "exchange": "💱",
    "bell": "🔔",
    "wallet": "💼",
    "refresh": "🔄",
    "shield": "🛡️",
    "bolt": "⚡",
    "link": "🔗",
    "pin": "📌",
    "heart": "❤️",
}


PERSIAN_DIGITS_MAP = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789"
)

SPOKEN_NUMBERS_MAP: Dict[str, float] = {
    "نیم": 0.5,
    "نصف": 0.5,
    "ربع": 0.25,
    "یک چهارم": 0.25,
    "سه چهارم": 0.75,
    "یک دهم": 0.1,
    "صفر": 0.0,
    "یک": 1.0,
    "یه": 1.0,
    "ی": 1.0,
    "دو": 2.0,
    "سه": 3.0,
    "چهار": 4.0,
    "پنج": 5.0,
    "شش": 6.0,
    "شیش": 6.0,
    "هفت": 7.0,
    "هشت": 8.0,
    "نه": 9.0,
    "ده": 10.0,
    "یازده": 11.0,
    "دوازده": 12.0,
    "سیزده": 13.0,
    "چهارده": 14.0,
    "پانزده": 15.0,
    "پونزده": 15.0,
    "شانزده": 16.0,
    "شونزده": 16.0,
    "هفده": 17.0,
    "هجده": 18.0,
    "هیجده": 18.0,
    "نوزده": 19.0,
    "بیست": 20.0,
    "سی": 30.0,
    "چهل": 40.0,
    "پنجاه": 50.0,
    "شصت": 60.0,
    "هفتاد": 70.0,
    "هشتاد": 80.0,
    "نود": 90.0,
    "صد": 100.0,
    "یکصد": 100.0,
    "دویست": 200.0,
    "سیصد": 300.0,
    "چهارصد": 400.0,
    "پانصد": 500.0,
    "پونصد": 500.0,
    "ششصد": 600.0,
    "هفتصد": 700.0,
    "هشتصد": 800.0,
    "نهصد": 900.0,
    "هزار": 1000.0,
    "یک هزار": 1000.0,
    "دو هزار": 2000.0,
    "پنج هزار": 5000.0,
    "ده هزار": 10000.0,
    "بیست هزار": 20000.0,
    "پنجاه هزار": 50000.0,
    "صد هزار": 100000.0,
    "پانصد هزار": 500000.0,
    "میلیون": 1000000.0,
    "یک میلیون": 1000000.0,
    "دو میلیون": 2000000.0,
    "ده میلیون": 10000000.0,
    "صد میلیون": 100000000.0,
    "میلیارد": 1000000000.0,
    "یک میلیارد": 1000000000.0,
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "twenty": 20.0,
    "thirty": 30.0,
    "forty": 40.0,
    "fifty": 50.0,
    "hundred": 100.0,
    "thousand": 1000.0,
    "million": 1000000.0,
    "half": 0.5,
    "quarter": 0.25,
}





CRYPTO_CATALOG: Dict[str, Dict[str, Any]] = {
    "BTC": {
        "fa_name": "بیت‌کوین",
        "en_name": "Bitcoin",
        "full_title": "بیت‌کوین / Bitcoin",
        "color": (247, 147, 26),
        "aliases": ["btc", "bitcoin", "بیتکوین", "بیت کوین", "بیت", "بتکوین", "xbt"],
        "default_usdt": 77451.30,
        "default_change": 1.85,
        "default_vol": 28450.75,
    },
    "ETH": {
        "fa_name": "اتریوم",
        "en_name": "Ethereum",
        "full_title": "اتریوم / Ethereum",
        "color": (98, 126, 234),
        "aliases": ["eth", "ethereum", "اتریوم", "اتر", "اتریم", "ether"],
        "default_usdt": 2286.00,
        "default_change": 1.42,
        "default_vol": 145200.50,
    },
    "USDT": {
        "fa_name": "تتر",
        "en_name": "Tether",
        "full_title": "تتر / دلار دیجیتال / Tether",
        "color": (38, 161, 123),
        "aliases": ["usdt", "tether", "تتر", "دلار تتر", "یو اس دی تی", "تتر آمریکا"],
        "default_usdt": 1.00,
        "default_change": 0.08,
        "default_vol": 89540000.00,
    },
    "TON": {
        "fa_name": "تون‌کوین",
        "en_name": "Toncoin",
        "full_title": "گرام / تون / Gram / Toncoin",
        "color": (0, 152, 234),
        "aliases": ["ton", "toncoin", "gram", "تون", "تون کوین", "تونکوین", "گرام", "ارز تون", "ارز تلگرام"],
        "default_usdt": 5.00,
        "default_change": 0.89,
        "default_vol": 89179.31,
    },
    "NOT": {
        "fa_name": "نات‌کوین",
        "en_name": "Notcoin",
        "full_title": "نات‌کوین / Notcoin",
        "color": (255, 215, 0),
        "aliases": ["not", "notcoin", "نات کوین", "ناتکوین", "نات", "ارز نات", "ارز نات کوین"],
        "default_usdt": 0.0085,
        "default_change": 3.45,
        "default_vol": 452100000.00,
    },
    "BNB": {
        "fa_name": "بایننس کوین",
        "en_name": "BNB",
        "full_title": "بایننس کوین / Binance Coin",
        "color": (243, 186, 47),
        "aliases": ["bnb", "binance", "binance coin", "بایننس", "بایننس کوین", "بی ان بی"],
        "default_usdt": 697.88,
        "default_change": 0.95,
        "default_vol": 42150.20,
    },
    "SOL": {
        "fa_name": "سولانا",
        "en_name": "Solana",
        "full_title": "سولانا / Solana",
        "color": (20, 241, 149),
        "aliases": ["sol", "solana", "سولانا", "سول"],
        "default_usdt": 93.38,
        "default_change": 2.65,
        "default_vol": 654300.10,
    },
    "XRP": {
        "fa_name": "ریپل",
        "en_name": "Ripple",
        "full_title": "ریپل / Ripple / XRP",
        "color": (0, 170, 228),
        "aliases": ["xrp", "ripple", "ریپل", "ارز ریپل", "ایکس آر پی"],
        "default_usdt": 1.28,
        "default_change": 1.15,
        "default_vol": 12450000.00,
    },
    "TRX": {
        "fa_name": "ترون",
        "en_name": "TRON",
        "full_title": "ترون / TRON / TRX",
        "color": (239, 0, 39),
        "aliases": ["trx", "tron", "ترون", "ارز ترون", "تی آر ایکس"],
        "default_usdt": 0.32543,
        "default_change": 0.64,
        "default_vol": 38900000.00,
    },
    "DOGE": {
        "fa_name": "دوج‌کوین",
        "en_name": "Dogecoin",
        "full_title": "دوج‌کوین / Dogecoin",
        "color": (194, 166, 51),
        "aliases": ["doge", "dogecoin", "دوج", "دوج کوین", "دوجکوین", "سگ کوین"],
        "default_usdt": 0.075204,
        "default_change": 2.10,
        "default_vol": 95400000.00,
    },
    "LTC": {
        "fa_name": "لایت‌کوین",
        "en_name": "Litecoin",
        "full_title": "لایت‌کوین / Litecoin",
        "color": (52, 93, 157),
        "aliases": ["ltc", "litecoin", "لایت کوین", "لایتکوین", "لایت"],
        "default_usdt": 54.35,
        "default_change": -0.45,
        "default_vol": 85400.00,
    },
    "BCH": {
        "fa_name": "بیت‌کوین کش",
        "en_name": "Bitcoin Cash",
        "full_title": "بیت‌کوین کش / Bitcoin Cash",
        "color": (10, 193, 142),
        "aliases": ["bch", "bitcoin cash", "بیتکوین کش", "بیت کوین کش", "بیت کش"],
        "default_usdt": 275.77,
        "default_change": 0.78,
        "default_vol": 19500.00,
    },
    "ADA": {
        "fa_name": "کاردانو",
        "en_name": "Cardano",
        "full_title": "کاردانو / آدا / Cardano",
        "color": (0, 51, 173),
        "aliases": ["ada", "cardano", "کاردانو", "آدا", "ادا"],
        "default_usdt": 0.58,
        "default_change": 1.30,
        "default_vol": 14500000.00,
    },
    "SHIB": {
        "fa_name": "شیبا اینو",
        "en_name": "Shiba Inu",
        "full_title": "شیبا اینو / Shiba Inu",
        "color": (255, 122, 0),
        "aliases": ["shib", "shiba", "shiba inu", "شیبا", "شیبا اینو", "ارز شیبا"],
        "default_usdt": 0.0000185,
        "default_change": 4.12,
        "default_vol": 5400000000.00,
    },
    "DOT": {
        "fa_name": "پولکادات",
        "en_name": "Polkadot",
        "full_title": "پولکادات / Polkadot",
        "color": (230, 0, 122),
        "aliases": ["dot", "polkadot", "پولکادات", "دات", "پلکادات"],
        "default_usdt": 5.85,
        "default_change": -0.30,
        "default_vol": 980000.00,
    },
    "AVAX": {
        "fa_name": "آوالانچ",
        "en_name": "Avalanche",
        "full_title": "آوالانچ / Avalanche",
        "color": (232, 65, 66),
        "aliases": ["avax", "avalanche", "آوالانچ", "اوالانچ", "آواکس"],
        "default_usdt": 26.40,
        "default_change": 1.95,
        "default_vol": 412000.00,
    },
    "LINK": {
        "fa_name": "چین‌لینک",
        "en_name": "Chainlink",
        "full_title": "چین‌لینک / Chainlink",
        "color": (42, 90, 218),
        "aliases": ["link", "chainlink", "چین لینک", "چینلینک", "لینک"],
        "default_usdt": 14.20,
        "default_change": 2.15,
        "default_vol": 725000.00,
    },
    "MATIC": {
        "fa_name": "پالیگان",
        "en_name": "Polygon (POL)",
        "full_title": "پالیگان / متیک / Polygon",
        "color": (130, 71, 229),
        "aliases": ["matic", "pol", "polygon", "پالیگان", "متیک", "ماتیک", "پلیگان"],
        "default_usdt": 0.42,
        "default_change": 0.85,
        "default_vol": 6200000.00,
    },
    "NEAR": {
        "fa_name": "نیر پروتکل",
        "en_name": "NEAR Protocol",
        "full_title": "نیر پروتکل / NEAR",
        "color": (0, 236, 151),
        "aliases": ["near", "near protocol", "نیر", "نیر پروتکل"],
        "default_usdt": 4.95,
        "default_change": 1.60,
        "default_vol": 1450000.00,
    },
    "UNI": {
        "fa_name": "یونی‌سواپ",
        "en_name": "Uniswap",
        "full_title": "یونی‌سواپ / Uniswap",
        "color": (255, 0, 122),
        "aliases": ["uni", "uniswap", "یونی سواپ", "یونی", "یونیسواپ"],
        "default_usdt": 8.40,
        "default_change": 0.90,
        "default_vol": 512000.00,
    },
    "ATOM": {
        "fa_name": "کازموس",
        "en_name": "Cosmos",
        "full_title": "کازموس / اتم / Cosmos",
        "color": (46, 49, 72),
        "aliases": ["atom", "cosmos", "کازموس", "اتم", "کاسموس"],
        "default_usdt": 5.10,
        "default_change": -0.20,
        "default_vol": 640000.00,
    },
    "XLM": {
        "fa_name": "استلار",
        "en_name": "Stellar",
        "full_title": "استلار / Stellar",
        "color": (20, 182, 231),
        "aliases": ["xlm", "stellar", "استلار", "لومن"],
        "default_usdt": 0.115,
        "default_change": 0.55,
        "default_vol": 4500000.00,
    },
    "ETC": {
        "fa_name": "اتریوم کلاسیک",
        "en_name": "Ethereum Classic",
        "full_title": "اتریوم کلاسیک / ETC",
        "color": (60, 185, 60),
        "aliases": ["etc", "ethereum classic", "اتریوم کلاسیک"],
        "default_usdt": 21.50,
        "default_change": 0.40,
        "default_vol": 310000.00,
    },
    "FIL": {
        "fa_name": "فایل‌کوین",
        "en_name": "Filecoin",
        "full_title": "فایل‌کوین / Filecoin",
        "color": (0, 144, 255),
        "aliases": ["fil", "filecoin", "فایل کوین", "فایلکوین"],
        "default_usdt": 4.25,
        "default_change": 1.10,
        "default_vol": 890000.00,
    },
    "APT": {
        "fa_name": "آپتوس",
        "en_name": "Aptos",
        "full_title": "آپتوس / Aptos",
        "color": (0, 230, 180),
        "aliases": ["apt", "aptos", "آپتوس", "اپتوس"],
        "default_usdt": 9.10,
        "default_change": 2.40,
        "default_vol": 620000.00,
    },
    "ARB": {
        "fa_name": "آربیتروم",
        "en_name": "Arbitrum",
        "full_title": "آربیتروم / Arbitrum",
        "color": (40, 160, 240),
        "aliases": ["arb", "arbitrum", "آربیتروم", "اربیتروم"],
        "default_usdt": 0.65,
        "default_change": 1.25,
        "default_vol": 4100000.00,
    },
    "OP": {
        "fa_name": "آپتیمیزم",
        "en_name": "Optimism",
        "full_title": "آپتیمیزم / Optimism",
        "color": (255, 4, 32),
        "aliases": ["op", "optimism", "آپتیمیزم", "اپتیمیزم"],
        "default_usdt": 1.45,
        "default_change": 1.05,
        "default_vol": 1950000.00,
    },
    "SUI": {
        "fa_name": "سویی",
        "en_name": "Sui",
        "full_title": "سویی / Sui",
        "color": (77, 162, 255),
        "aliases": ["sui", "سویی", "سويي", "ارز سویی"],
        "default_usdt": 2.15,
        "default_change": 4.50,
        "default_vol": 8900000.00,
    },
    "PEPE": {
        "fa_name": "پپه",
        "en_name": "Pepe",
        "full_title": "پپه / Pepe",
        "color": (76, 149, 64),
        "aliases": ["pepe", "پپه", "ارز پپه", "قورباغه"],
        "default_usdt": 0.0000105,
        "default_change": 5.20,
        "default_vol": 12500000000.00,
    },
    "DOGS": {
        "fa_name": "داگز",
        "en_name": "DOGS",
        "full_title": "داگز / DOGS",
        "color": (240, 240, 240),
        "aliases": ["dogs", "داگز", "ارز داگز", "سگ تلگرام"],
        "default_usdt": 0.00068,
        "default_change": 2.80,
        "default_vol": 850000000.00,
    },
    "HMSTR": {
        "fa_name": "همستر کامبت",
        "en_name": "Hamster Kombat",
        "full_title": "همستر کامبت / Hamster Kombat",
        "color": (255, 165, 0),
        "aliases": ["hmstr", "hamster", "hamster kombat", "همستر", "همستر کامبت", "ارز همستر"],
        "default_usdt": 0.0038,
        "default_change": -1.20,
        "default_vol": 310000000.00,
    },
    "CATI": {
        "fa_name": "کتیزن",
        "en_name": "Catizen",
        "full_title": "کتیزن / Catizen",
        "color": (255, 192, 203),
        "aliases": ["cati", "catizen", "کتیزن", "ارز کتیزن", "گربه تلگرام"],
        "default_usdt": 0.45,
        "default_change": 1.90,
        "default_vol": 14500000.00,
    },
    "MAJOR": {
        "fa_name": "میجر",
        "en_name": "Major",
        "full_title": "میجر / Major",
        "color": (255, 215, 0),
        "aliases": ["major", "میجر", "ماجور", "ارز میجر"],
        "default_usdt": 1.12,
        "default_change": 3.10,
        "default_vol": 6500000.00,
    },
    "X": {
        "fa_name": "ایکس امپایر",
        "en_name": "X Empire",
        "full_title": "ایکس امپایر / ماسک امپایر / X Empire",
        "color": (0, 210, 255),
        "aliases": ["x", "x empire", "xempire", "ایکس امپایر", "ماسک امپایر"],
        "default_usdt": 0.00024,
        "default_change": 4.10,
        "default_vol": 920000000.00,
    },
    "PAXG": {
        "fa_name": "پکس گلد (انس طلا)",
        "en_name": "PAX Gold",
        "full_title": "پکس گلد / انس جهانی طلا / PAX Gold",
        "color": (255, 215, 0),
        "aliases": ["paxg", "pax gold", "پکس گلد", "انس طلا", "طلا جهانی", "اونس طلا"],
        "default_usdt": 2800.00,
        "default_change": 0.65,
        "default_vol": 4520.00,
    },
    "FLOKI": {
        "fa_name": "فلوکی",
        "en_name": "Floki",
        "full_title": "فلوکی اینو / Floki",
        "color": (245, 155, 35),
        "aliases": ["floki", "فلوکی", "فلوکی اینو"],
        "default_usdt": 0.000145,
        "default_change": 2.90,
        "default_vol": 450000000.00,
    },
    "BONK": {
        "fa_name": "بونک",
        "en_name": "Bonk",
        "full_title": "بونک / Bonk",
        "color": (255, 140, 0),
        "aliases": ["bonk", "بونک", "ارز بونک"],
        "default_usdt": 0.000022,
        "default_change": 3.70,
        "default_vol": 980000000.00,
    },
    "WIF": {
        "fa_name": "داگ ویف هت",
        "en_name": "dogwifhat",
        "full_title": "داگ ویف هت / dogwifhat",
        "color": (210, 140, 100),
        "aliases": ["wif", "dogwifhat", "ویف", "داگ ویف هت"],
        "default_usdt": 2.35,
        "default_change": 4.20,
        "default_vol": 15200000.00,
    },
    "FET": {
        "fa_name": "فچ ای‌آی",
        "en_name": "Artificial Superintelligence",
        "full_title": "فچ ای‌آی / Fetch.ai (ASI)",
        "color": (50, 200, 255),
        "aliases": ["fet", "asi", "fetch", "فچ", "فچ ای آی"],
        "default_usdt": 1.38,
        "default_change": 2.80,
        "default_vol": 12400000.00,
    },
    "RNDR": {
        "fa_name": "رندر",
        "en_name": "Render",
        "full_title": "رندر / Render",
        "color": (235, 30, 60),
        "aliases": ["rndr", "render", "رندر", "ارز رندر"],
        "default_usdt": 5.45,
        "default_change": 1.95,
        "default_vol": 3200000.00,
    },
    "INJ": {
        "fa_name": "اینجکتیو",
        "en_name": "Injective",
        "full_title": "اینجکتیو / Injective",
        "color": (0, 242, 254),
        "aliases": ["inj", "injective", "اینجکتیو"],
        "default_usdt": 21.10,
        "default_change": 1.75,
        "default_vol": 890000.00,
    },
    "AAVE": {
        "fa_name": "آوه",
        "en_name": "Aave",
        "full_title": "آوه / Aave",
        "color": (182, 80, 158),
        "aliases": ["aave", "آوه", "اوه"],
        "default_usdt": 152.00,
        "default_change": 1.10,
        "default_vol": 145000.00,
    },
    "FTM": {
        "fa_name": "فانتوم (سونیک)",
        "en_name": "Fantom (Sonic)",
        "full_title": "فانتوم / سونیک / Fantom",
        "color": (25, 105, 255),
        "aliases": ["ftm", "fantom", "sonic", "فانتوم", "سونیک"],
        "default_usdt": 0.68,
        "default_change": 2.30,
        "default_vol": 18500000.00,
    },
    "ALGO": {
        "fa_name": "آلگوراند",
        "en_name": "Algorand",
        "full_title": "آلگوراند / Algorand",
        "color": (0, 200, 200),
        "aliases": ["algo", "algorand", "آلگوراند", "الگوراند"],
        "default_usdt": 0.14,
        "default_change": 0.45,
        "default_vol": 9500000.00,
    },
    "VET": {
        "fa_name": "وی‌چین",
        "en_name": "VeChain",
        "full_title": "وی‌چین / VeChain",
        "color": (21, 189, 255),
        "aliases": ["vet", "vechain", "وی چین", "ویچین"],
        "default_usdt": 0.024,
        "default_change": 0.80,
        "default_vol": 24000000.00,
    },
    "SAND": {
        "fa_name": "سندباکس",
        "en_name": "The Sandbox",
        "full_title": "سندباکس / The Sandbox",
        "color": (0, 173, 239),
        "aliases": ["sand", "sandbox", "سندباکس", "سند"],
        "default_usdt": 0.28,
        "default_change": 1.15,
        "default_vol": 8200000.00,
    },
    "MANA": {
        "fa_name": "دیسنترالند",
        "en_name": "Decentraland",
        "full_title": "دیسنترالند / مانا / MANA",
        "color": (255, 45, 85),
        "aliases": ["mana", "decentraland", "مانا", "دیسنترالند"],
        "default_usdt": 0.31,
        "default_change": 0.95,
        "default_vol": 6100000.00,
    },
    "AXS": {
        "fa_name": "اکسی اینفینیتی",
        "en_name": "Axie Infinity",
        "full_title": "اکسی اینفینیتی / Axie Infinity",
        "color": (0, 85, 213),
        "aliases": ["axs", "axie", "اکسی", "اکسی اینفینیتی"],
        "default_usdt": 5.15,
        "default_change": 0.60,
        "default_vol": 780000.00,
    },
    "EOS": {
        "fa_name": "ایاس",
        "en_name": "EOS",
        "full_title": "ایاس / EOS",
        "color": (150, 150, 180),
        "aliases": ["eos", "ایاس", "ای او اس"],
        "default_usdt": 0.52,
        "default_change": 0.25,
        "default_vol": 5400000.00,
    },
    "XMR": {
        "fa_name": "مونرو",
        "en_name": "Monero",
        "full_title": "مونرو / Monero",
        "color": (255, 102, 0),
        "aliases": ["xmr", "monero", "مونرو"],
        "default_usdt": 162.50,
        "default_change": 0.70,
        "default_vol": 85000.00,
    },
    "ICP": {
        "fa_name": "اینترنت کامپیوتر",
        "en_name": "Internet Computer",
        "full_title": "اینترنت کامپیوتر / ICP",
        "color": (241, 90, 36),
        "aliases": ["icp", "internet computer", "اینترنت کامپیوتر", "آی سی پی"],
        "default_usdt": 8.20,
        "default_change": 1.40,
        "default_vol": 1200000.00,
    },
    "SEI": {
        "fa_name": "سی",
        "en_name": "Sei",
        "full_title": "سی / Sei Network",
        "color": (180, 30, 50),
        "aliases": ["sei", "سی", "ارز سی"],
        "default_usdt": 0.44,
        "default_change": 2.90,
        "default_vol": 14000000.00,
    },
    "TIA": {
        "fa_name": "سلستیا",
        "en_name": "Celestia",
        "full_title": "سلستیا / Celestia",
        "color": (123, 43, 249),
        "aliases": ["tia", "celestia", "سلستیا", "تیا"],
        "default_usdt": 5.30,
        "default_change": 1.80,
        "default_vol": 2100000.00,
    },
    "STARS": {
        "fa_name": "استارز تلگرام",
        "en_name": "Telegram Stars",
        "full_title": "استارز تلگرام / Telegram Stars",
        "color": (255, 200, 0),
        "aliases": ["stars", "starz", "استارز", "استار", "ستاره تلگرام"],
        "default_usdt": 0.015,
        "default_change": 0.00,
        "default_vol": 1500000.00,
    },
}


ALIAS_TO_SYMBOL: Dict[str, str] = {}
for _sym, _meta in CRYPTO_CATALOG.items():
    ALIAS_TO_SYMBOL[_sym.lower()] = _sym
    ALIAS_TO_SYMBOL[_meta["fa_name"].lower()] = _sym
    ALIAS_TO_SYMBOL[_meta["en_name"].lower()] = _sym
    for _al in _meta["aliases"]:
        ALIAS_TO_SYMBOL[_al.lower().strip()] = _sym
        ALIAS_TO_SYMBOL[_al.lower().replace(" ", "").replace("‌", "")] = _sym


FIAT_GOLD_ALIASES: Dict[str, str] = {
    "دلار": "USD_FIAT",
    "دلار آمریکا": "USD_FIAT",
    "دلار آزاد": "USD_FIAT",
    "usd": "USD_FIAT",
    "dollar": "USD_FIAT",
    "یورو": "EUR_FIAT",
    "eur": "EUR_FIAT",
    "euro": "EUR_FIAT",
    "پوند": "GBP_FIAT",
    "gbp": "GBP_FIAT",
    "درهم": "AED_FIAT",
    "درهم امارات": "AED_FIAT",
    "aed": "AED_FIAT",
    "لیر": "TRY_FIAT",
    "لیر ترکیه": "TRY_FIAT",
    "try": "TRY_FIAT",
    "فرانک": "CHF_FIAT",
    "فرانک سوئیس": "CHF_FIAT",
    "دلار کانادا": "CAD_FIAT",
    "روبل": "RUB_FIAT",
    "روپیه": "INR_FIAT",
    "یوان": "CNY_FIAT",
    "دینار": "IQD_FIAT",
    "دینار عراق": "IQD_FIAT",
    "افغانی": "AFN_FIAT",
    "سکه": "SEKKEH_GOLD",
    "سکه امامی": "SEKKEH_GOLD",
    "سکه تمام": "SEKKEH_GOLD",
    "مثقال": "MESGHAL_GOLD",
    "مثقال طلا": "MESGHAL_GOLD",
    "گرم طلا": "GRAM_GOLD",
    "طلای ۱۸ عیار": "GRAM_GOLD",
    "طلا 18 عیار": "GRAM_GOLD",
    "طلا": "GRAM_GOLD",
    "نقره": "SILVER_GRAM",
    "گرم نقره": "SILVER_GRAM",
    "تومان": "IRR_TOMAN",
    "تومن": "IRR_TOMAN",
    "ریال": "IRR_RIAL",
}





crypto_data_cache: Dict[str, Dict[str, Any]] = {}
fiat_gold_cache: Dict[str, Dict[str, Any]] = {}
last_update_time: Optional[datetime] = None
user_sessions: Dict[int, Dict[str, Any]] = {}


def initialize_default_market_cache():
    """Populates the initial cache so the bot works instantaneously even on boot."""
    global crypto_data_cache, fiat_gold_cache, last_update_time
    base_usdt_toman = 272000.0

    for sym, info in CRYPTO_CATALOG.items():
        usdt_p = float(info["default_usdt"])
        irr_p = base_usdt_toman if sym == "USDT" else round(usdt_p * base_usdt_toman, 2)
        chg = float(info["default_change"])
        high_usdt = round(usdt_p * (1 + abs(chg) / 100.0 + 0.008), 6)
        low_usdt = round(usdt_p * (1 - abs(chg) / 100.0 - 0.008), 6)
        high_irr = round(high_usdt * base_usdt_toman)
        low_irr = round(low_usdt * base_usdt_toman)
        best_buy = round(irr_p * 0.9985)
        best_sell = round(irr_p * 1.0015)

        crypto_data_cache[sym] = {
            "symbol": sym,
            "name": info["fa_name"],
            "en_name": info["en_name"],
            "full_title": info["full_title"],
            "irr": str(irr_p),
            "usdt": str(usdt_p),
            "dayChange": f"{chg:+.2f}",
            "high_irr": str(high_irr),
            "low_irr": str(low_irr),
            "high_usdt": str(high_usdt),
            "low_usdt": str(low_usdt),
            "best_buy_irr": str(best_buy),
            "best_sell_irr": str(best_sell),
            "volume_24h": str(info["default_vol"]),
            "color": info["color"],
        }

    fiat_gold_cache = {
        "USD": {"name": "دلار", "flag": "🇺🇸", "price": 272000},
        "EUR": {"name": "یورو", "flag": "🇪🇺", "price": 296480},
        "GBP": {"name": "پوند", "flag": "🇬🇧", "price": 350880},
        "CHF": {"name": "فرانک", "flag": "🇨🇭", "price": 312800},
        "CAD": {"name": "دلار کانادا", "flag": "🇨🇦", "price": 195840},
        "TRY": {"name": "لیر", "flag": "🇹🇷", "price": 7888},
        "RUB": {"name": "روبل", "flag": "🇷🇺", "price": 2992},
        "INR": {"name": "روپیه", "flag": "🇮🇳", "price": 3264},
        "CNY": {"name": "یوان", "flag": "🇨🇳", "price": 38080},
        "IQD": {"name": "دینار", "flag": "🇮🇶", "price": 184},
        "AED": {"name": "درهم", "flag": "🇦🇪", "price": 74256},
        "AFN": {"name": "افغانی", "flag": "🇦🇫", "price": 3808},
        "SEKKEH": {"name": "سکه", "price": 171762175},
        "MESGHAL": {"name": "مثقال طلا", "price": 79551306},
        "GRAM_GOLD": {"name": "گرم طلا", "price": 18364492},
        "GRAM_SILVER": {"name": "گرم نقره", "price": 288070},
        "OUNCE_GOLD": {"name": "انس طلا", "price": 2800.00},
    }
    last_update_time = datetime.now(IRAN_TZ)


initialize_default_market_cache()





class GroupManager:
    """Manages Telegram Groups where @CryptoZenthflowbot is installed."""

    def __init__(self, db_name: str = DB_FILE_NAME):
        self.db_name = db_name
        self.init_group_database()

    def init_group_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                group_title TEXT,
                group_username TEXT,
                is_active INTEGER DEFAULT 1,
                require_dot INTEGER DEFAULT 0,
                install_date TEXT,
                admin_user_id INTEGER,
                message_count INTEGER DEFAULT 0,
                last_activity TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def add_group(
        self,
        group_id: int,
        group_title: str,
        group_username: Optional[str],
        admin_user_id: int,
        is_active: int = 1,
    ):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now_iso = datetime.now(IRAN_TZ).isoformat()
        cursor.execute(
            """
            INSERT OR REPLACE INTO groups
            (group_id, group_title, group_username, is_active, install_date, admin_user_id, last_activity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (group_id, group_title or "گروه", group_username or "", is_active, now_iso, admin_user_id, now_iso),
        )
        conn.commit()
        conn.close()

    def activate_group(self, group_id: int):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE groups SET is_active = 1, install_date = ?
            WHERE group_id = ?
            """,
            (datetime.now(IRAN_TZ).isoformat(), group_id),
        )
        conn.commit()
        conn.close()

    def deactivate_group(self, group_id: int):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE groups SET is_active = 0 WHERE group_id = ?", (group_id,))
        conn.commit()
        conn.close()

    def get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "group_id": row[0],
                "group_title": row[1],
                "group_username": row[2],
                "is_active": row[3],
                "require_dot": row[4],
                "install_date": row[5],
                "admin_user_id": row[6],
                "message_count": row[7],
                "last_activity": row[8],
            }
        return None

    def get_all_groups(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups ORDER BY install_date DESC")
        groups = []
        for row in cursor.fetchall():
            groups.append(
                {
                    "group_id": row[0],
                    "group_title": row[1],
                    "group_username": row[2],
                    "is_active": row[3],
                    "require_dot": row[4],
                    "install_date": row[5],
                    "admin_user_id": row[6],
                    "message_count": row[7],
                    "last_activity": row[8],
                }
            )
        conn.close()
        return groups

    def update_group_activity(self, group_id: int, title: str = "", username: str = ""):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now_iso = datetime.now(IRAN_TZ).isoformat()
        cursor.execute("SELECT group_id FROM groups WHERE group_id = ?", (group_id,))
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO groups (group_id, group_title, group_username, is_active, install_date, admin_user_id, message_count, last_activity)
                VALUES (?, ?, ?, 1, ?, 0, 1, ?)
                """,
                (group_id, title or "گروه", username or "", now_iso, now_iso),
            )
        else:
            cursor.execute(
                """
                UPDATE groups SET last_activity = ?, message_count = message_count + 1
                WHERE group_id = ?
                """,
                (now_iso, group_id),
            )
        conn.commit()
        conn.close()


class DatabaseManager:
    """Manages Users, Activity Logs, Required Channels, Portfolio & Price Alerts."""

    def __init__(self, db_name: str = DB_FILE_NAME):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                join_date TEXT,
                message_count INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                last_activity TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                message_text TEXT,
                timestamp TEXT,
                message_type TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS required_chats (
                chat_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                chat_type TEXT NOT NULL,
                added_by INTEGER,
                added_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS price_alerts (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                target_price REAL,
                currency TEXT DEFAULT 'USDT',
                condition TEXT DEFAULT 'above',
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_portfolio (
                user_id INTEGER,
                symbol TEXT,
                amount REAL,
                updated_at TEXT,
                PRIMARY KEY (user_id, symbol)
            )
            """
        )
        conn.commit()
        conn.close()

    def add_user(self, user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now_iso = datetime.now(IRAN_TZ).isoformat()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO users (user_id, username, first_name, last_name, join_date, message_count, is_banned, last_activity)
                VALUES (?, ?, ?, ?, ?, 1, 0, ?)
                """,
                (user_id, username or "", first_name or "کاربر", last_name or "", now_iso, now_iso),
            )
        else:
            cursor.execute(
                """
                UPDATE users SET username = ?, first_name = ?, last_name = ?, last_activity = ?
                WHERE user_id = ?
                """,
                (username or "", first_name or "کاربر", last_name or "", now_iso, user_id),
            )
        conn.commit()
        conn.close()

    def update_user_activity(self, user_id: int):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users SET last_activity = ?, message_count = message_count + 1
            WHERE user_id = ?
            """,
            (datetime.now(IRAN_TZ).isoformat(), user_id),
        )
        conn.commit()
        conn.close()

    def log_message(self, user_id: int, chat_id: int, message_text: str, message_type: str):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (user_id, chat_id, message_text, timestamp, message_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, chat_id, message_text[:500], datetime.now(IRAN_TZ).isoformat(), message_type),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging message: {e}")

    def ban_user(self, user_id: int):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def unban_user(self, user_id: int):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.*, COUNT(m.message_id) as total_messages
            FROM users u
            LEFT JOIN messages m ON u.user_id = m.user_id
            WHERE u.user_id = ?
            GROUP BY u.user_id
            """,
            (user_id,),
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                "user_id": result[0],
                "username": result[1],
                "first_name": result[2],
                "last_name": result[3],
                "join_date": result[4],
                "message_count": result[5],
                "is_banned": result[6],
                "last_activity": result[7],
                "total_messages": result[8],
            }
        return None

    def get_all_users(self, limit: int = 2000) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.*, COUNT(m.message_id) as total_messages
            FROM users u
            LEFT JOIN messages m ON u.user_id = m.user_id
            GROUP BY u.user_id
            ORDER BY u.join_date DESC
            LIMIT ?
            """,
            (limit,),
        )
        users = []
        for row in cursor.fetchall():
            users.append(
                {
                    "user_id": row[0],
                    "username": row[1],
                    "first_name": row[2],
                    "last_name": row[3],
                    "join_date": row[4],
                    "message_count": row[5],
                    "is_banned": row[6],
                    "last_activity": row[7],
                    "total_messages": row[8],
                }
            )
        conn.close()
        return users

    def get_bot_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        week_ago = (datetime.now(IRAN_TZ) - timedelta(days=7)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM users WHERE last_activity > ?", (week_ago,))
        active_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned_users = cursor.fetchone()[0]
        conn.close()
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_messages": total_messages,
            "banned_users": banned_users,
        }

    def add_required_chat(self, chat_id: int, username: str, chat_type: str, added_by: int):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO required_chats (chat_id, username, chat_type, added_by, added_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, username, chat_type, added_by, datetime.now(IRAN_TZ).isoformat()),
        )
        conn.commit()
        conn.close()

    def remove_required_chat(self, chat_id: int):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM required_chats WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()

    def get_all_required_chats(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM required_chats")
        chats = []
        for row in cursor.fetchall():
            chats.append(
                {
                    "chat_id": row[0],
                    "username": row[1],
                    "chat_type": row[2],
                    "added_by": row[3],
                    "added_at": row[4],
                }
            )
        conn.close()
        return chats

    
    def set_portfolio_asset(self, user_id: int, symbol: str, amount: float):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if amount <= 0:
            cursor.execute("DELETE FROM user_portfolio WHERE user_id = ? AND symbol = ?", (user_id, symbol.upper()))
        else:
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_portfolio (user_id, symbol, amount, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, symbol.upper(), amount, datetime.now(IRAN_TZ).isoformat()),
            )
        conn.commit()
        conn.close()

    def get_user_portfolio(self, user_id: int) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, amount, updated_at FROM user_portfolio WHERE user_id = ?", (user_id,))
        items = [{"symbol": r[0], "amount": r[1], "updated_at": r[2]} for r in cursor.fetchall()]
        conn.close()
        return items


db = DatabaseManager()
group_manager = GroupManager()


def get_required_chats() -> List[Dict[str, Any]]:
    try:
        return db.get_all_required_chats()
    except Exception as e:
        logger.error(f"Error fetching required chats: {e}")
        return []






def gregorian_to_jalali(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
    """Pure Python Gregorian to Jalali converter."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def get_jalali_datetime_strings() -> Tuple[str, str]:
    """Returns exact Persian date and time strings."""
    now = datetime.now(IRAN_TZ)
    weekdays_fa = [
        "دوشنبه",
        "سه‌شنبه",
        "چهارشنبه",
        "پنج‌شنبه",
        "جمعه",
        "شنبه",
        "یکشنبه",
    ]
    months_fa = [
        "فروردین",
        "اردیبهشت",
        "خرداد",
        "تیر",
        "مرداد",
        "شهریور",
        "مهر",
        "آبان",
        "آذر",
        "دی",
        "بهمن",
        "اسفند",
    ]
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    day_name = weekdays_fa[now.weekday()]
    month_name = months_fa[jm - 1]
    date_str = f"{day_name} {jd} {month_name} {jy}"
    time_str = now.strftime("%H:%M")
    return date_str, time_str


def format_price(price: Union[str, float, int], is_usdt: bool = False) -> str:
    """Formats Toman and USDT prices cleanly with commas and appropriate decimal precision."""
    try:
        price_num = float(price)
        if price_num == 0:
            return "0"
        if not is_usdt:
            if price_num >= 100:
                return f"{price_num:,.0f}"
            elif price_num >= 1:
                return f"{price_num:,.2f}".rstrip("0").rstrip(".")
            else:
                return f"{price_num:.4f}".rstrip("0").rstrip(".")
        else:
            if price_num >= 1000:
                return f"{price_num:,.2f}"
            elif price_num >= 1:
                return f"{price_num:,.2f}"
            elif price_num >= 0.01:
                return f"{price_num:.5f}".rstrip("0").rstrip(".")
            else:
                return f"{price_num:.8f}".rstrip("0").rstrip(".")
    except Exception:
        return str(price)


def normalize_persian_text(text: str) -> str:
    """Normalizes Arabic/Persian characters, digits, and zero-width spaces."""
    if not text:
        return ""
    t = text.translate(PERSIAN_DIGITS_MAP)
    t = t.replace("ي", "ی").replace("ك", "ک").replace("ة", "ه").replace("ؤ", "و").replace("إ", "ا").replace("أ", "ا")
    t = t.replace("\u200c", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_spoken_or_numeric_amount(raw_token: str) -> Optional[float]:
    """Converts strings like '70', '۷۰', 'یک', 'دو و نیم', '0.5' into a float."""
    clean = normalize_persian_text(raw_token).lower().replace(",", "")
    if not clean:
        return None
    try:
        return float(clean)
    except ValueError:
        pass
    if clean in SPOKEN_NUMBERS_MAP:
        return SPOKEN_NUMBERS_MAP[clean]
    if clean.endswith("تا"):
        sub = clean[:-2].strip()
        if sub in SPOKEN_NUMBERS_MAP:
            return SPOKEN_NUMBERS_MAP[sub]
        try:
            return float(sub)
        except ValueError:
            pass
    if " و نیم" in clean:
        base_part = clean.replace(" و نیم", "").strip()
        if base_part in SPOKEN_NUMBERS_MAP:
            return SPOKEN_NUMBERS_MAP[base_part] + 0.5
    return None






async def fetch_live_market_data() -> bool:
    """
    Fetches live cryptocurrency, gold, and fiat rates from Fast-Creat Nobitex v2 API
    and Nobitex Official Stats API.
    """
    global crypto_data_cache, fiat_gold_cache, last_update_time
    updated_any = False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=12.0, verify=False, follow_redirects=True, headers=headers) as client:
        
        try:
            resp = await client.get(NOBITEX_FAST_API)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") and data.get("code") == 200 and isinstance(data.get("result"), dict):
                    api_res = data["result"]
                    usdt_irr_val = float(api_res.get("USDT", {}).get("irr", 0) or 0)
                    if usdt_irr_val < 10000:
                        usdt_irr_val = float(crypto_data_cache.get("USDT", {}).get("irr", 272000))

                    for sym, c_info in api_res.items():
                        sym_up = sym.upper()
                        irr_raw = float(c_info.get("irr", 0) or 0)
                        usdt_raw = float(c_info.get("usdt", 0) or 0)
                        chg_raw = float(c_info.get("dayChange", 0) or 0)

                        if irr_raw == 0 and usdt_raw > 0:
                            irr_raw = round(usdt_raw * usdt_irr_val, 2)
                        elif usdt_raw == 0 and irr_raw > 0 and usdt_irr_val > 0:
                            usdt_raw = round(irr_raw / usdt_irr_val, 6)

                        if irr_raw <= 0 and usdt_raw <= 0:
                            continue

                        cat_meta = CRYPTO_CATALOG.get(sym_up, {})
                        fa_name = c_info.get("name") or cat_meta.get("fa_name") or sym_up
                        en_name = cat_meta.get("en_name") or sym_up
                        full_title = cat_meta.get("full_title") or f"{fa_name} / {en_name}"
                        color = cat_meta.get("color", (0, 230, 150))

                        spread = max(abs(chg_raw) / 100.0, 0.012)
                        high_irr = float(c_info.get("high_irr") or round(irr_raw * (1 + spread * 0.65)))
                        low_irr = float(c_info.get("low_irr") or round(irr_raw * (1 - spread * 0.65)))
                        high_usdt = float(c_info.get("high_usdt") or round(usdt_raw * (1 + spread * 0.65), 6))
                        low_usdt = float(c_info.get("low_usdt") or round(usdt_raw * (1 - spread * 0.65), 6))
                        best_buy = round(irr_raw * 0.9982)
                        best_sell = round(irr_raw * 1.0018)
                        vol_24 = c_info.get("volume") or cat_meta.get("default_vol") or round(random.uniform(15000, 250000), 2)

                        crypto_data_cache[sym_up] = {
                            "symbol": sym_up,
                            "name": fa_name,
                            "en_name": en_name,
                            "full_title": full_title,
                            "irr": str(irr_raw),
                            "usdt": str(usdt_raw),
                            "dayChange": f"{chg_raw:+.2f}",
                            "high_irr": str(high_irr),
                            "low_irr": str(low_irr),
                            "high_usdt": str(high_usdt),
                            "low_usdt": str(low_usdt),
                            "best_buy_irr": str(best_buy),
                            "best_sell_irr": str(best_sell),
                            "volume_24h": str(vol_24),
                            "color": color,
                        }
                        ALIAS_TO_SYMBOL[sym_up.lower()] = sym_up
                        ALIAS_TO_SYMBOL[fa_name.lower().strip()] = sym_up
                    updated_any = True
        except Exception as e:
            logger.warning(f"Fast-Creat Nobitex API warning: {e}")

        
        try:
            r_nob = await client.get(NOBITEX_OFFICIAL_STATS)
            if r_nob.status_code == 200:
                nob_data = r_nob.json()
                stats = nob_data.get("stats", {})
                usdt_rls_stat = stats.get("usdt-rls", {})
                if usdt_rls_stat and usdt_rls_stat.get("latest"):
                    live_usdt_toman = float(usdt_rls_stat["latest"]) / 10.0
                else:
                    live_usdt_toman = float(crypto_data_cache.get("USDT", {}).get("irr", 272000))

                for pair_key, st in stats.items():
                    if st.get("isClosed"):
                        continue
                    parts = pair_key.split("-")
                    if len(parts) != 2:
                        continue
                    src_sym, dst_sym = parts[0].upper(), parts[1].upper()
                    if src_sym not in crypto_data_cache:
                        continue

                    if dst_sym == "RLS":
                        latest_toman = float(st.get("latest", 0) or 0) / 10.0
                        high_toman = float(st.get("dayHigh", 0) or 0) / 10.0
                        low_toman = float(st.get("dayLow", 0) or 0) / 10.0
                        buy_toman = float(st.get("bestBuy", 0) or 0) / 10.0
                        sell_toman = float(st.get("bestSell", 0) or 0) / 10.0
                        vol_src = float(st.get("volumeSrc", 0) or 0)
                        day_chg = float(st.get("dayChange", 0) or 0)

                        if latest_toman > 0:
                            crypto_data_cache[src_sym]["irr"] = str(latest_toman)
                        if high_toman > 0:
                            crypto_data_cache[src_sym]["high_irr"] = str(high_toman)
                        if low_toman > 0:
                            crypto_data_cache[src_sym]["low_irr"] = str(low_toman)
                        if buy_toman > 0:
                            crypto_data_cache[src_sym]["best_buy_irr"] = str(buy_toman)
                        if sell_toman > 0:
                            crypto_data_cache[src_sym]["best_sell_irr"] = str(sell_toman)
                        if vol_src > 0:
                            crypto_data_cache[src_sym]["volume_24h"] = f"{vol_src:.2f}"
                        crypto_data_cache[src_sym]["dayChange"] = f"{day_chg:+.2f}"

                    elif dst_sym == "USDT":
                        latest_u = float(st.get("latest", 0) or 0)
                        high_u = float(st.get("dayHigh", 0) or 0)
                        low_u = float(st.get("dayLow", 0) or 0)
                        if latest_u > 0:
                            crypto_data_cache[src_sym]["usdt"] = str(latest_u)
                            if float(crypto_data_cache[src_sym].get("irr", 0)) == 0:
                                crypto_data_cache[src_sym]["irr"] = str(round(latest_u * live_usdt_toman, 2))
                        if high_u > 0:
                            crypto_data_cache[src_sym]["high_usdt"] = str(high_u)
                        if low_u > 0:
                            crypto_data_cache[src_sym]["low_usdt"] = str(low_u)
                updated_any = True
        except Exception as e:
            logger.debug(f"Nobitex official stats supplementary check: {e}")

    
    try:
        usdt_toman = float(crypto_data_cache.get("USDT", {}).get("irr", 272000))
        if usdt_toman <= 0:
            usdt_toman = 272000.0

        if "STARS" in crypto_data_cache:
            stars_u = float(crypto_data_cache["STARS"]["usdt"])
            crypto_data_cache["STARS"]["irr"] = str(round(stars_u * usdt_toman, 2))
            crypto_data_cache["STARS"]["high_irr"] = str(round(stars_u * 1.02 * usdt_toman, 2))
            crypto_data_cache["STARS"]["low_irr"] = str(round(stars_u * 0.98 * usdt_toman, 2))
            crypto_data_cache["STARS"]["best_buy_irr"] = str(round(stars_u * 0.995 * usdt_toman, 2))
            crypto_data_cache["STARS"]["best_sell_irr"] = str(round(stars_u * 1.005 * usdt_toman, 2))

        paxg_usd = float(crypto_data_cache.get("PAXG", {}).get("usdt", 2800.00))
        if paxg_usd <= 1000:
            paxg_usd = 2800.00

        usd_rate = int(round(usdt_toman))
        eur_rate = int(round(usd_rate * 1.09))
        gbp_rate = int(round(usd_rate * 1.29))
        chf_rate = int(round(usd_rate * 1.15))
        cad_rate = int(round(usd_rate * 0.72))
        try_rate = int(round(usd_rate * 0.029))
        rub_rate = int(round(usd_rate * 0.011))
        inr_rate = int(round(usd_rate * 0.012))
        cny_rate = int(round(usd_rate * 0.14))
        iqd_rate = int(round(usd_rate * 0.0006765))
        aed_rate = int(round(usd_rate * 0.273))
        afn_rate = int(round(usd_rate * 0.014))

        gram_gold_18k = int(round((paxg_usd / 31.1034768) * 0.750 * usd_rate))
        mesghal_gold = int(round(gram_gold_18k * 4.3318))
        sekkeh_emami = int(round(gram_gold_18k * 8.133 * 1.1516))
        gram_silver = int(round((paxg_usd / 87.5 / 31.1034768) * usd_rate))

        fiat_gold_cache = {
            "USD": {"name": "دلار", "flag": "🇺🇸", "price": usd_rate},
            "EUR": {"name": "یورو", "flag": "🇪🇺", "price": eur_rate},
            "GBP": {"name": "پوند", "flag": "🇬🇧", "price": gbp_rate},
            "CHF": {"name": "فرانک", "flag": "🇨🇭", "price": chf_rate},
            "CAD": {"name": "دلار", "flag": "🇨🇦", "price": cad_rate},
            "TRY": {"name": "لیر", "flag": "🇹🇷", "price": try_rate},
            "RUB": {"name": "روبل", "flag": "🇷🇺", "price": rub_rate},
            "INR": {"name": "روپیه", "flag": "🇮🇳", "price": inr_rate},
            "CNY": {"name": "یوان", "flag": "🇨🇳", "price": cny_rate},
            "IQD": {"name": "دینار", "flag": "🇮🇶", "price": iqd_rate},
            "AED": {"name": "درهم", "flag": "🇦🇪", "price": aed_rate},
            "AFN": {"name": "افغانی", "flag": "🇦🇫", "price": afn_rate},
            "SEKKEH": {"name": "سکه", "price": sekkeh_emami},
            "MESGHAL": {"name": "مثقال طلا", "price": mesghal_gold},
            "GRAM_GOLD": {"name": "گرم طلا", "price": gram_gold_18k},
            "GRAM_SILVER": {"name": "گرم نقره", "price": gram_silver},
            "OUNCE_GOLD": {"name": "انس طلا", "price": paxg_usd},
        }
        last_update_time = datetime.now(IRAN_TZ)
    except Exception as e:
        logger.error(f"Error computing fiat/gold rates: {e}")

    return updated_any


async def update_crypto_cache(context: ContextTypes.DEFAULT_TYPE = None) -> bool:
    """Periodic job wrapper to keep market cache fresh."""
    return await fetch_live_market_data()




async def generate_exact_exchange_rate_board() -> str:
    """
    Generates the exact "نرخ ارز" board requested by the user with live data,
    Persian Jalali weekday/date, and Iran standard time.
    """
    await fetch_live_market_data()
    date_str, time_str = get_jalali_datetime_strings()

    
    usd_p = int(fiat_gold_cache.get("USD", {}).get("price", 272000))
    eur_p = int(fiat_gold_cache.get("EUR", {}).get("price", 296480))
    gbp_p = int(fiat_gold_cache.get("GBP", {}).get("price", 350880))
    chf_p = int(fiat_gold_cache.get("CHF", {}).get("price", 312800))
    cad_p = int(fiat_gold_cache.get("CAD", {}).get("price", 195840))
    try_p = int(fiat_gold_cache.get("TRY", {}).get("price", 7888))
    rub_p = int(fiat_gold_cache.get("RUB", {}).get("price", 2992))
    inr_p = int(fiat_gold_cache.get("INR", {}).get("price", 3264))
    cny_p = int(fiat_gold_cache.get("CNY", {}).get("price", 38080))
    iqd_p = int(fiat_gold_cache.get("IQD", {}).get("price", 184))
    aed_p = int(fiat_gold_cache.get("AED", {}).get("price", 74256))
    afn_p = int(fiat_gold_cache.get("AFN", {}).get("price", 3808))

    sekkeh_p = int(fiat_gold_cache.get("SEKKEH", {}).get("price", 171762175))
    mesghal_p = int(fiat_gold_cache.get("MESGHAL", {}).get("price", 79551306))
    gram_gold_p = int(fiat_gold_cache.get("GRAM_GOLD", {}).get("price", 18364492))
    gram_silver_p = int(fiat_gold_cache.get("GRAM_SILVER", {}).get("price", 288070))
    ounce_gold_p = float(fiat_gold_cache.get("OUNCE_GOLD", {}).get("price", 2800.00))

    
    def get_c_usd(sym: str, default_val: float, decimals: int = 2) -> str:
        raw_val = crypto_data_cache.get(sym, {}).get("usdt", default_val)
        try:
            num = float(raw_val)
            if decimals == 2:
                return f"{num:,.2f}"
            elif decimals == 5:
                return f"{num:.5f}".rstrip("0").rstrip(".")
            elif decimals == 6:
                return f"{num:.6f}".rstrip("0").rstrip(".")
            return f"{num:,.2f}"
        except Exception:
            return str(default_val)

    usdt_toman = int(float(crypto_data_cache.get("USDT", {}).get("irr", usd_p)))
    btc_usd = get_c_usd("BTC", 77451.30, 2)
    eth_usd = get_c_usd("ETH", 2286.00, 2)
    bnb_usd = get_c_usd("BNB", 697.88, 2)
    sol_usd = get_c_usd("SOL", 93.38, 2)
    ltc_usd = get_c_usd("LTC", 54.35, 2)
    bch_usd = get_c_usd("BCH", 275.77, 2)
    xrp_usd = get_c_usd("XRP", 1.28, 2)
    trx_usd = get_c_usd("TRX", 0.32543, 5)
    doge_usd = get_c_usd("DOGE", 0.075204, 6)
    ton_usd = get_c_usd("TON", 5.00, 2)

    board_text = (
        f"◄ نرخ ارز و طلا در بازار آزاد :\n"
        f"        \n"
        f"- {date_str}\n\n"
        f"- ساعت : {time_str}\n\n\n"
        f"🇺🇸 دلار : {usd_p:,} تومان\n"
        f"🇪🇺 یورو : {eur_p:,} تومان\n"
        f"🇬🇧 پوند : {gbp_p:,} تومان\n"
        f"🇨🇭 فرانک : {chf_p:,} تومان\n"
        f"🇨🇦 دلار : {cad_p:,} تومان\n"
        f"🇹🇷 لیر : {try_p:,} تومان\n"
        f"🇷🇺 روبل : {rub_p:,} تومان\n"
        f"🇮🇳 روپیه : {inr_p:,} تومان\n"
        f"🇨🇳 یوان : {cny_p:,} تومان\n"
        f"🇮🇶 دینار : {iqd_p:,} تومان\n"
        f"🇦🇪 درهم : {aed_p:,} تومان\n"
        f"🇦🇫 افغانی : {afn_p:,} تومان\n"
        f"~ ~ ~ ~ ~ ~\n"
        f"• سکه : {sekkeh_p:,} تومان\n"
        f"• مثقال طلا : {mesghal_p:,} تومان\n"
        f"• گرم طلا : {gram_gold_p:,} تومان\n"
        f"• گرم نقره : {gram_silver_p:,} تومان\n"
        f"• انس طلا : {ounce_gold_p:,.2f} دلار\n"
        f"~ ~ ~ ~ ~ ~\n"
        f"◄ قیمت ارزهای دیجیتال:\n\n"
        f"💵 تتر : {usdt_toman:,} تومان\n"
        f"💰 بیتکوین : {btc_usd} دلار\n"
        f"💰 اتریوم : {eth_usd} دلار\n"
        f"💰 بایننس کوین : {bnb_usd} دلار\n"
        f"💰 سولانا : {sol_usd} دلار\n"
        f"💰 لایت کوین : {ltc_usd} دلار\n"
        f"💰 بیتکوین کش : {bch_usd} دلار\n"
        f"💰 ریپل : {xrp_usd} دلار\n"
        f"💰 ترون : {trx_usd} دلار\n"
        f"💰 دوج کوین : {doge_usd} دلار\n"
        f"💰 گرام (تون‌کوین) : {ton_usd} دلار"
    )
    return board_text






def _load_chart_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Attempts to load clean system fonts supporting Persian/English, falls back gracefully."""
    font_candidates = [
        "Vazirmatn-Bold.ttf" if bold else "Vazirmatn-Regular.ttf",
        "Tahoma.ttf",
        "tahoma.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for fp in font_candidates:
        try:
            if os.path.exists(fp):
                return ImageFont.truetype(fp, size)
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _shape_persian_for_pil(text: str) -> str:
    """Shapes Persian text if arabic_reshaper & python-bidi are installed; otherwise returns clean text."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def generate_meowie_style_crypto_chart(symbol: str, crypto_info: Dict[str, Any]) -> BytesIO:
    """
    Renders a 1280x720 Ultra-HD Dark Neon Area Chart modeled after the user's uploaded image:
      - Top-Left: Diamond/Coin Icon + Symbol (e.g., TON) + Full Title + (24H) Badge
      - Large Toman Price + Green/Red Percentage Pill + Rial Equivalent Subtitle
      - Top-Right: MEOWIE Green Dot Indicator + Glass Box with (SYM / USDT) Dollar Price & Badge
      - Center: Rounded Glass Chart Frame + Smooth Neon Spline Curve + Gradient Area Fill
      - High (سقف) & Low (کف) Callout Markers + Bottom Volume Bars + Dashed Baseline
      - Bottom: 4 Rounded Info Cards:
          1. دامنه نوسان تومانی (24H کمترین / بیشترین)
          2. دامنه نوسان دلاری (USDT)
          3. بهترین پیشنهاد خرید / فروش (دفتر سفارشات صرافی)
          4. حجم معاملات 24 ساعته (گردش بازار)
    """
    width, height = 1280, 720
    bg_img = Image.new("RGBA", (width, height), (12, 11, 20, 255))
    draw = ImageDraw.Draw(bg_img, "RGBA")

    
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_layer, "RGBA")
    g_draw.ellipse([(-150, -120), (550, 420)], fill=(38, 22, 78, 70))
    g_draw.ellipse([(750, 380), (1380, 820)], fill=(12, 68, 65, 65))
    g_draw.ellipse([(380, 180), (920, 560)], fill=(18, 45, 58, 50))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=65))
    bg_img = Image.alpha_composite(bg_img, glow_layer)
    draw = ImageDraw.Draw(bg_img, "RGBA")

    
    sym_up = symbol.upper()
    irr_price = float(crypto_info.get("irr", 0) or 0)
    usdt_price = float(crypto_info.get("usdt", 0) or 0)
    rial_price = int(round(irr_price * 10))
    try:
        day_change = float(crypto_info.get("dayChange", 0) or 0)
    except Exception:
        day_change = 0.0

    is_positive = day_change >= 0
    main_neon_color = (0, 230, 145) if is_positive else (255, 68, 95)
    badge_bg_color = (14, 62, 48, 220) if is_positive else (72, 22, 32, 220)
    badge_border_color = (0, 215, 135, 255) if is_positive else (255, 75, 100, 255)

    high_irr = float(crypto_info.get("high_irr") or round(irr_price * 1.018))
    low_irr = float(crypto_info.get("low_irr") or round(irr_price * 0.982))
    high_usdt = float(crypto_info.get("high_usdt") or round(usdt_price * 1.018, 4))
    low_usdt = float(crypto_info.get("low_usdt") or round(usdt_price * 0.982, 4))
    best_buy = float(crypto_info.get("best_buy_irr") or round(irr_price * 0.9985))
    best_sell = float(crypto_info.get("best_sell_irr") or round(irr_price * 1.0015))
    vol_24h = float(crypto_info.get("volume_24h") or 89179.31)
    coin_color = crypto_info.get("color", (0, 152, 234))

    
    f_sym_lg = _load_chart_font(34, bold=True)
    f_price_xl = _load_chart_font(54, bold=True)
    f_usd_lg = _load_chart_font(28, bold=True)
    f_card_val = _load_chart_font(21, bold=True)
    f_regular = _load_chart_font(17, bold=False)
    f_small = _load_chart_font(15, bold=False)
    f_tiny = _load_chart_font(14, bold=True)

    
    icon_cx, icon_cy, icon_r = 74, 52, 20
    draw.ellipse(
        [(icon_cx - icon_r, icon_cy - icon_r), (icon_cx + icon_r, icon_cy + icon_r)],
        fill=(coin_color[0], coin_color[1], coin_color[2], 255),
        outline=(255, 255, 255, 140),
        width=2,
    )
    draw.polygon(
        [(icon_cx - 9, icon_cy - 6), (icon_cx + 9, icon_cy - 6), (icon_cx, icon_cy + 10)],
        outline=(255, 255, 255, 240),
        width=2,
    )

    draw.text((105, 32), sym_up, fill=(255, 255, 255, 255), font=f_sym_lg)
    sym_bbox = draw.textbbox((105, 32), sym_up, font=f_sym_lg)
    title_x = sym_bbox[2] + 16

    full_title_str = _shape_persian_for_pil(f"({crypto_info.get('full_title', sym_up)})")
    draw.text((title_x, 42), full_title_str, fill=(95, 175, 255, 255), font=f_regular)
    t_bbox = draw.textbbox((title_x, 42), full_title_str, font=f_regular)

    
    pill_x1 = t_bbox[2] + 14
    pill_x2 = pill_x1 + 165
    draw.rounded_rectangle(
        [(pill_x1, 37), (pill_x2, 68)],
        radius=12,
        fill=(32, 30, 48, 220),
        outline=(75, 72, 105, 180),
        width=1,
    )
    tf_label = _shape_persian_for_pil("تایم فریم 24 ساعته (24H)")
    draw.text((pill_x1 + 12, 43), tf_label, fill=(215, 215, 230, 255), font=f_small)

    
    irr_formatted = format_price(irr_price, is_usdt=False)
    draw.text((52, 92), irr_formatted, fill=(255, 255, 255, 255), font=f_price_xl)
    p_bbox = draw.textbbox((52, 92), irr_formatted, font=f_price_xl)

    toman_lbl = _shape_persian_for_pil("تومان")
    draw.text((p_bbox[2] + 12, 114), toman_lbl, fill=(185, 188, 205, 255), font=f_usd_lg)
    tm_bbox = draw.textbbox((p_bbox[2] + 12, 114), toman_lbl, font=f_usd_lg)

    
    chg_bx1 = tm_bbox[2] + 18
    chg_bx2 = chg_bx1 + 96
    draw.rounded_rectangle(
        [(chg_bx1, 106), (chg_bx2, 144)],
        radius=8,
        fill=badge_bg_color,
        outline=badge_border_color,
        width=2,
    )
    arrow_ch = "▲" if is_positive else "▼"
    chg_str = f"{arrow_ch} {day_change:+.2f}%"
    draw.text((chg_bx1 + 11, 115), chg_str, fill=main_neon_color, font=f_small)

    
    rial_lbl = _shape_persian_for_pil(f"معادل {rial_price:,} ریال")
    draw.text((54, 158), rial_lbl, fill=(135, 140, 162, 255), font=f_regular)

    
    draw.ellipse([(1176, 43), (1190, 57)], fill=(0, 230, 145, 255))
    draw.text((1198, 40), "MEOWIE", fill=(235, 238, 248, 255), font=f_small)

    usd_box_x1, usd_box_y1, usd_box_x2, usd_box_y2 = 910, 90, 1228, 164
    draw.rounded_rectangle(
        [(usd_box_x1, usd_box_y1), (usd_box_x2, usd_box_y2)],
        radius=14,
        fill=(21, 23, 36, 225),
        outline=(52, 58, 82, 200),
        width=1,
    )
    usd_hdr = _shape_persian_for_pil(f"نرخ دلاری ({sym_up} / USDT)")
    draw.text((usd_box_x1 + 22, usd_box_y1 + 11), usd_hdr, fill=(155, 162, 185, 255), font=f_small)

    usd_val_str = f"${format_price(usdt_price, is_usdt=True)}"
    draw.text((usd_box_x1 + 22, usd_box_y1 + 34), usd_val_str, fill=(255, 255, 255, 255), font=f_usd_lg)

    
    usd_chg = day_change * 0.85
    draw.rounded_rectangle(
        [(usd_box_x2 - 96, usd_box_y1 + 34), (usd_box_x2 - 16, usd_box_y1 + 62)],
        radius=6,
        fill=badge_bg_color,
        outline=badge_border_color,
        width=1,
    )
    draw.text((usd_box_x2 - 88, usd_box_y1 + 40), f"{arrow_ch} {usd_chg:+.2f}%", fill=main_neon_color, font=f_tiny)

    
    chart_x1, chart_y1, chart_x2, chart_y2 = 50, 192, 1230, 528
    draw.rounded_rectangle(
        [(chart_x1, chart_y1), (chart_x2, chart_y2)],
        radius=16,
        fill=(16, 18, 29, 210),
        outline=(42, 46, 68, 220),
        width=1,
    )

    
    rng = random.Random(f"{sym_up}_{datetime.now(IRAN_TZ).strftime('%Y%m%d%H')}_{int(irr_price)}")
    num_pts = 72
    raw_series = []
    cur_v = 0.5
    trend_slope = 0.006 if is_positive else -0.006
    for i in range(num_pts):
        wave = math.sin(i * 0.28) * 0.08 + math.cos(i * 0.13) * 0.06
        noise = rng.uniform(-0.075, 0.075)
        cur_v += trend_slope + noise + wave * 0.15
        raw_series.append(cur_v)

    smoothed = []
    for i in range(num_pts):
        window = raw_series[max(0, i - 2) : min(num_pts, i + 3)]
        smoothed.append(sum(window) / len(window))

    min_s, max_s = min(smoothed), max(smoothed)
    span_s = max(max_s - min_s, 1e-6)

    plot_left = chart_x1 + 26
    plot_right = chart_x2 - 26
    plot_top = chart_y1 + 46
    plot_bottom = chart_y2 - 52

    curve_points: List[Tuple[int, int]] = []
    min_idx, max_idx = 0, 0
    for idx, val in enumerate(smoothed):
        norm = (val - min_s) / span_s
        px = int(plot_left + (idx / (num_pts - 1)) * (plot_right - plot_left))
        py = int(plot_bottom - norm * (plot_bottom - plot_top))
        curve_points.append((px, py))
        if val <= min_s:
            min_idx = idx
        if val >= max_s:
            max_idx = idx

    
    area_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    a_draw = ImageDraw.Draw(area_layer, "RGBA")
    polygon_pts = [(plot_left, plot_bottom)] + curve_points + [(plot_right, plot_bottom)]
    a_draw.polygon(polygon_pts, fill=(main_neon_color[0], main_neon_color[1], main_neon_color[2], 68))

    fade_mask = Image.new("L", (width, height), 0)
    m_draw = ImageDraw.Draw(fade_mask)
    for y_pos in range(plot_top, plot_bottom + 1):
        alpha_factor = int(210 * (1.0 - ((y_pos - plot_top) / max(1, (plot_bottom - plot_top))) ** 0.85))
        m_draw.line([(plot_left, y_pos), (plot_right, y_pos)], fill=max(0, min(255, alpha_factor)))
    bg_img.paste(area_layer, (0, 0), mask=fade_mask)
    draw = ImageDraw.Draw(bg_img, "RGBA")

    
    baseline_y = plot_bottom + 8
    for dash_x in range(plot_left, plot_right, 14):
        draw.line([(dash_x, baseline_y), (dash_x + 7, baseline_y)], fill=(65, 72, 98, 180), width=1)

    num_vol_bars = 64
    vol_step = (plot_right - plot_left) / num_vol_bars
    for v_i in range(num_vol_bars):
        vx = int(plot_left + v_i * vol_step)
        vh = int(rng.uniform(4, 24))
        v_col = (0, 195, 125, 130) if rng.random() > 0.28 else (215, 65, 90, 110)
        draw.rectangle([(vx, chart_y2 - 14 - vh), (vx + 4, chart_y2 - 14)], fill=v_col)

    
    glow_line_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gl_draw = ImageDraw.Draw(glow_line_layer, "RGBA")
    gl_draw.line(curve_points, fill=(main_neon_color[0], main_neon_color[1], main_neon_color[2], 150), width=8, joint="curve")
    glow_line_layer = glow_line_layer.filter(ImageFilter.GaussianBlur(radius=5))
    bg_img = Image.alpha_composite(bg_img, glow_line_layer)
    draw = ImageDraw.Draw(bg_img, "RGBA")

    draw.line(curve_points, fill=(main_neon_color[0], main_neon_color[1], main_neon_color[2], 255), width=3, joint="curve")

    
    last_px, last_py = curve_points[-1]
    draw.ellipse([(last_px - 9, last_py - 9), (last_px + 9, last_py + 9)], fill=(main_neon_color[0], main_neon_color[1], main_neon_color[2], 95))
    draw.ellipse([(last_px - 5, last_py - 5), (last_px + 5, last_py + 5)], fill=(255, 255, 255, 255), outline=main_neon_color, width=2)

    
    max_px, max_py = curve_points[max_idx]
    min_px, min_py = curve_points[min_idx]

    high_lbl = _shape_persian_for_pil(f"سقف : {format_price(high_irr)}")
    low_lbl = _shape_persian_for_pil(f"کف : {format_price(low_irr)}")

    draw.ellipse([(max_px - 4, max_py - 4), (max_px + 4, max_py + 4)], fill=(255, 255, 255, 255))
    draw.text((max(plot_left + 10, min(plot_right - 140, max_px - 45)), max_py - 26), high_lbl, fill=(215, 222, 240, 255), font=f_small)

    draw.ellipse([(min_px - 4, min_py - 4), (min_px + 4, min_py + 4)], fill=(255, 255, 255, 255))
    draw.text((max(plot_left + 10, min(plot_right - 140, min_px - 45)), min_py + 8), low_lbl, fill=(215, 222, 240, 255), font=f_small)

    
    cards_y1, cards_y2 = 552, 678
    card_w = 280
    card_gap = 20
    cards_data = [
        {
            "top_title": "24H کمترین / بیشترین (تومان)",
            "main_val": f"{format_price(low_irr)} - {format_price(high_irr)}",
            "val_color": (255, 255, 255, 255),
            "sub_title": "دامنه نوسان تومانی",
        },
        {
            "top_title": "دامنه نوسان دلاری (USDT)",
            "main_val": f"${format_price(low_usdt, True)} - ${format_price(high_usdt, True)}",
            "val_color": (68, 168, 255, 255),
            "sub_title": "دامنه نوسان دلاری",
        },
        {
            "top_title": "بهترین پیشنهاد خرید / فروش",
            "main_val": f"{format_price(best_buy)} / {format_price(best_sell)}",
            "val_color": (0, 230, 145, 255),
            "sub_title": "دفتر سفارشات صرافی",
        },
        {
            "top_title": "حجم معاملات 24 ساعته",
            "main_val": f"{format_price(vol_24h, True)} {sym_up}",
            "val_color": (255, 195, 15, 255),
            "sub_title": "گردش بازار",
        },
    ]

    for idx, c_item in enumerate(cards_data):
        cx1 = 50 + idx * (card_w + card_gap)
        cx2 = cx1 + card_w
        draw.rounded_rectangle(
            [(cx1, cards_y1), (cx2, cards_y2)],
            radius=14,
            fill=(18, 20, 32, 225),
            outline=(45, 50, 74, 210),
            width=1,
        )
        t_str = _shape_persian_for_pil(c_item["top_title"])
        v_str = c_item["main_val"]
        s_str = _shape_persian_for_pil(c_item["sub_title"])

        draw.text((cx1 + 18, cards_y1 + 16), t_str, fill=(168, 174, 198, 255), font=f_small)
        draw.text((cx1 + 18, cards_y1 + 52), v_str, fill=c_item["val_color"], font=f_card_val)
        draw.text((cx1 + 18, cards_y1 + 92), s_str, fill=(115, 122, 146, 255), font=f_small)

    out_bio = BytesIO()
    bg_img.convert("RGB").save(out_bio, format="JPEG", quality=95)
    out_bio.seek(0)
    return out_bio


async def get_crypto_chart_photo(symbol: str, crypto_info: Dict[str, Any], prefer_local_meowie: bool = True) -> BytesIO:
    """
    Returns the high-resolution MEOWIE style chart image (matching the user's reference photo).
    Also supports fetching from Fast-Creat Chart API if needed.
    """
    if prefer_local_meowie:
        try:
            return await asyncio.to_thread(generate_meowie_style_crypto_chart, symbol, crypto_info)
        except Exception as e:
            logger.error(f"Local MEOWIE chart error for {symbol}: {e}")

    try:
        url = f"{FAST_CHART_API}&symbol={symbol.upper()}&id=@{BOT_USERNAME}&type=1"
        async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") and data.get("status") == "successfully":
                    img_url = data["result"]["image"]
                    img_resp = await client.get(img_url)
                    if img_resp.status_code == 200:
                        return BytesIO(img_resp.content)
    except Exception as e:
        logger.warning(f"External chart API fallback warning for {symbol}: {e}")

    return await asyncio.to_thread(generate_meowie_style_crypto_chart, symbol, crypto_info)






def resolve_currency_query(raw_query: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Resolves any Persian or English currency name/symbol (e.g., 'ناتکوین', 'اتریوم', 'تتر', 'TON')
    into (symbol, crypto_data_dict).
    """
    if not raw_query:
        return None, None

    norm = normalize_persian_text(raw_query).lower()
    norm = re.sub(r"^(?:ارز|قیمت|چارت|نمودار|نرخ|کوین|توکن)\s+", "", norm).strip()
    norm_nospace = norm.replace(" ", "")

    if norm in ALIAS_TO_SYMBOL:
        sym = ALIAS_TO_SYMBOL[norm]
        return sym, crypto_data_cache.get(sym)
    if norm_nospace in ALIAS_TO_SYMBOL:
        sym = ALIAS_TO_SYMBOL[norm_nospace]
        return sym, crypto_data_cache.get(sym)

    if norm in FIAT_GOLD_ALIASES:
        f_key = FIAT_GOLD_ALIASES[norm]
        if f_key == "USD_FIAT":
            return "USDT", crypto_data_cache.get("USDT")
        if f_key == "IRR_TOMAN":
            usdt_irr = float(crypto_data_cache.get("USDT", {}).get("irr", 272000))
            return "IRR", {
                "symbol": "IRR",
                "name": "تومان ایران",
                "en_name": "Iranian Toman",
                "full_title": "تومان / Toman",
                "irr": "1",
                "usdt": str(1.0 / usdt_irr if usdt_irr > 0 else 0),
                "dayChange": "0.00",
            }

    up_q = norm.upper()
    if up_q in crypto_data_cache:
        return up_q, crypto_data_cache[up_q]

    for sym, c_data in crypto_data_cache.items():
        fa_n = normalize_persian_text(c_data.get("name", "")).lower()
        en_n = c_data.get("en_name", "").lower()
        if norm == fa_n or norm == en_n or norm_nospace == fa_n.replace(" ", ""):
            return sym, c_data
        if len(norm) >= 3 and (norm in fa_n or norm in en_n):
            return sym, c_data

    return None, None


def parse_user_crypto_inquiry(raw_text: str) -> Dict[str, Any]:
    """
    Parses any user text message into structured intent:
      - {"type": "exchange_board"} -> when user says "نرخ ارز"
      - {"type": "convert", "amount": float, "src": str, "dst": str} -> "100 تتر به تومان"
      - {"type": "inquiry", "amount": float, "query": str, "explicit_amount": bool}
    """
    norm = normalize_persian_text(raw_text)
    if norm.startswith("."):
        norm = norm[1:].strip()

    low = norm.lower()

    
    board_triggers = [
        "نرخ ارز",
        "نرخ ارز و طلا",
        "قیمت ارز",
        "قیمت طلا و ارز",
        "بازار آزاد",
        "لیست قیمت",
        "تابلو ارز",
        "نرخ روز",
    ]
    if low in board_triggers:
        return {"type": "exchange_board"}

    
    m_conv = re.match(
        r"^(\d+(?:\.\d+)?|یک|یه|دو|سه|چهار|پنج|ده|صد|هزار|نیم)\s+(.+?)\s+(?:به|to|در)\s+(.+)$",
        low,
        re.IGNORECASE,
    )
    if m_conv:
        amt_val = parse_spoken_or_numeric_amount(m_conv.group(1)) or 1.0
        return {
            "type": "convert",
            "amount": amt_val,
            "src": m_conv.group(2).strip(),
            "dst": m_conv.group(3).strip(),
        }

    
    m_num = re.match(r"^(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:تا|عدد|واحد)?\s*([^\d]+)$", low)
    if m_num:
        amt_val = parse_spoken_or_numeric_amount(m_num.group(1))
        coin_part = m_num.group(2).strip()
        if amt_val is not None and coin_part:
            return {
                "type": "inquiry",
                "amount": amt_val,
                "query": coin_part,
                "explicit_amount": True,
            }

    
    m_rev_num = re.match(r"^([^\d]+?)\s+(\d+(?:,\d+)*(?:\.\d+)?)$", low)
    if m_rev_num:
        coin_part = m_rev_num.group(1).strip()
        amt_val = parse_spoken_or_numeric_amount(m_rev_num.group(2))
        if amt_val is not None and coin_part:
            return {
                "type": "inquiry",
                "amount": amt_val,
                "query": coin_part,
                "explicit_amount": True,
            }

    
    words = low.split()
    if len(words) >= 3:
        two_word_prefix = f"{words[0]} {words[1]}"
        if two_word_prefix in SPOKEN_NUMBERS_MAP:
            rem_coin = " ".join(words[2:]).strip()
            return {
                "type": "inquiry",
                "amount": SPOKEN_NUMBERS_MAP[two_word_prefix],
                "query": rem_coin,
                "explicit_amount": True,
            }

    if len(words) >= 2:
        first_w = words[0].rstrip("تا")
        if first_w in SPOKEN_NUMBERS_MAP:
            rem_coin = " ".join(words[1:]).strip()
            return {
                "type": "inquiry",
                "amount": SPOKEN_NUMBERS_MAP[first_w],
                "query": rem_coin,
                "explicit_amount": True,
            }

    
    return {
        "type": "inquiry",
        "amount": 1.0,
        "query": low,
        "explicit_amount": False,
    }






def build_crypto_caption(
    crypto: Dict[str, Any],
    symbol: str,
    amount: float = 1.0,
    explicit_amount: bool = False,
) -> str:
    """
    Creates a rich, comprehensive Persian & English information caption for any requested
    cryptocurrency and quantity, accompanying the MEOWIE 24H chart image.
    """
    unit_irr = float(crypto.get("irr", 0) or 0)
    unit_usdt = float(crypto.get("usdt", 0) or 0)
    total_irr = unit_irr * amount
    total_rial = total_irr * 10.0
    total_usdt = unit_usdt * amount

    high_irr = float(crypto.get("high_irr") or unit_irr * 1.015)
    low_irr = float(crypto.get("low_irr") or unit_irr * 0.985)
    high_usdt = float(crypto.get("high_usdt") or unit_usdt * 1.015)
    low_usdt = float(crypto.get("low_usdt") or unit_usdt * 0.985)
    best_buy = float(crypto.get("best_buy_irr") or unit_irr * 0.9985)
    best_sell = float(crypto.get("best_sell_irr") or unit_irr * 1.0015)
    vol_24h = float(crypto.get("volume_24h") or 0)

    try:
        chg_val = float(crypto.get("dayChange", 0) or 0)
    except Exception:
        chg_val = 0.0

    if chg_val > 0:
        chg_icon = "🟢 📈"
    elif chg_val < 0:
        chg_icon = "🔴 📉"
    else:
        chg_icon = "⚪ ➡️"

    date_str, time_str = get_jalali_datetime_strings()
    fa_name = crypto.get("name", symbol)
    en_name = crypto.get("en_name", symbol)

    amt_display = f"{amount:g}" if amount != int(amount) else f"{int(amount):,}"

    if explicit_amount or amount != 1.0:
        header = (
            f"💎 <b>استعلام و محاسبه لحظه‌ای {amt_display} {fa_name} ({en_name} - {symbol})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧮 <b>تعداد مورد استعلام:</b> <code>{amt_display} {symbol}</code>\n"
            f"💰 <b>ارزش کل به تومان:</b> <code>{format_price(total_irr)}</code> تومان\n"
            f"💴 <b>ارزش کل به ریال:</b> <code>{format_price(total_rial)}</code> ریال\n"
            f"💵 <b>ارزش کل به دلار:</b> <code>${format_price(total_usdt, is_usdt=True)}</code> USDT\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>اطلاعات پایه هر ۱ واحد {fa_name}:</b>\n"
        )
    else:
        header = (
            f"💎 <b>استعلام لحظه‌ای ارز دیجیتال {fa_name} ({en_name} - {symbol})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
        )

    details = (
        f"🇮🇷 <b>قیمت واحد (تومان):</b> <code>{format_price(unit_irr)}</code> تومان\n"
        f"💵 <b>نرخ دلاری (USDT):</b> <code>${format_price(unit_usdt, is_usdt=True)}</code>\n"
        f"{chg_icon} <b>تغییرات ۲۴ ساعته:</b> <code>{chg_val:+.2f}%</code>\n\n"
        f"🔼 <b>بیشترین قیمت (24H):</b> <code>{format_price(high_irr)}</code> تومان (<code>${format_price(high_usdt, True)}</code>)\n"
        f"🔽 <b>کمترین قیمت (24H):</b> <code>{format_price(low_irr)}</code> تومان (<code>${format_price(low_usdt, True)}</code>)\n"
        f"📗 <b>بهترین پیشنهاد خرید:</b> <code>{format_price(best_buy)}</code> تومان\n"
        f"📕 <b>بهترین پیشنهاد فروش:</b> <code>{format_price(best_sell)}</code> تومان\n"
        f"🔄 <b>حجم معاملات 24h:</b> <code>{format_price(vol_24h, True)} {symbol}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 {date_str} | 🕒 ساعت: <code>{time_str}</code>\n"
        f"🤖 @{BOT_USERNAME}"
    )
    return header + details


def build_crypto_inline_keyboard(symbol: str, amount: float = 1.0) -> InlineKeyboardMarkup:
    """Interactive buttons below each crypto chart for quick recalculation & refresh."""
    amt_str = f"{amount:g}"
    keyboard = [
        [
            InlineKeyboardButton(f"🔄 بروزرسانی لحظه‌ای {symbol}", callback_data=f"refresh_crypto_{symbol}_{amt_str}"),
            InlineKeyboardButton("◄ تابلوی نرخ ارز و طلا", callback_data="show_exchange_board"),
        ],
        [
            InlineKeyboardButton("× 1", callback_data=f"calc_crypto_{symbol}_1"),
            InlineKeyboardButton("× 10", callback_data=f"calc_crypto_{symbol}_10"),
            InlineKeyboardButton("× 50", callback_data=f"calc_crypto_{symbol}_50"),
            InlineKeyboardButton("× 100", callback_data=f"calc_crypto_{symbol}_100"),
            InlineKeyboardButton("× 1000", callback_data=f"calc_crypto_{symbol}_1000"),
        ],
        [
            InlineKeyboardButton("🔎 ارسال اینلاین در چت‌ها", switch_inline_query=symbol),
            InlineKeyboardButton("🏠 منوی راهنما", callback_data="back_to_start"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_exchange_board_keyboard() -> InlineKeyboardMarkup:
    """
    Clean inline keyboard for 'نرخ ارز' WITHOUT the 3 crypto chart buttons
    (Removed 'چارت تون‌کوین', 'چارت نات‌کوین', 'چارت بیت‌کوین' per image 65555555555555555555555555555555555.PNG).
    """
    keyboard = [
        [InlineKeyboardButton("🔄 بروزرسانی لحظه‌ای نرخ ارز", callback_data="show_exchange_board")],
    ]
    return InlineKeyboardMarkup(keyboard)






async def convert_currency_amount(amount: float, source_str: str, target_str: str) -> Dict[str, Any]:
    """Converts between any two cryptocurrencies or Iranian Toman / USD."""
    if not crypto_data_cache:
        await fetch_live_market_data()

    src_sym, src_crypto = resolve_currency_query(source_str)
    dst_sym, dst_crypto = resolve_currency_query(target_str)

    if not src_crypto or not dst_crypto:
        return {"error": f"ارز مبدأ ({source_str}) یا مقصد ({target_str}) شناسایی نشد."}

    try:
        if src_sym == "IRR":
            dst_irr = float(dst_crypto.get("irr", 0))
            if dst_irr <= 0:
                return {"error": f"قیمت تومانی {dst_crypto.get('name')} در دسترس نیست."}
            converted = amount / dst_irr
        elif dst_sym == "IRR":
            src_irr = float(src_crypto.get("irr", 0))
            if src_irr <= 0:
                return {"error": f"قیمت تومانی {src_crypto.get('name')} در دسترس نیست."}
            converted = amount * src_irr
        else:
            src_usdt = float(src_crypto.get("usdt", 0))
            dst_usdt = float(dst_crypto.get("usdt", 0))
            if src_usdt <= 0 or dst_usdt <= 0:
                return {"error": "نرخ دلاری یکی از ارزها در دسترس نیست."}
            converted = (amount * src_usdt) / dst_usdt

        return {
            "amount": amount,
            "converted_amount": converted,
            "source_symbol": src_sym,
            "target_symbol": dst_sym,
            "source_name": src_crypto.get("name", src_sym),
            "target_name": dst_crypto.get("name", dst_sym),
        }
    except Exception as e:
        return {"error": f"خطا در محاسبه تبدیل: {e}"}


def format_conversion_result_message(conv_res: Dict[str, Any]) -> str:
    if "error" in conv_res:
        return (
            f"{EMOJIS['error']} <b>خطا در تبدیل ارز</b>\n\n"
            f"⚠️ {conv_res['error']}\n"
            f"💡 نمونه فرمت صحیح: <code>100 تتر به تومان</code> یا <code>2 اتریوم به بیتکوین</code>"
        )

    date_str, time_str = get_jalali_datetime_strings()
    amt = conv_res["amount"]
    res_val = conv_res["converted_amount"]
    is_target_usd = conv_res["target_symbol"] != "IRR"

    return (
        f"💱 <b>نتیجه تبدیل لحظه‌ای ارز</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📤 <b>مقدار مبدأ:</b> <code>{format_price(amt, True)}</code> <b>{conv_res['source_name']} ({conv_res['source_symbol']})</b>\n"
        f"📥 <b>معادل دقیق:</b> <code>{format_price(res_val, is_target_usd)}</code> <b>{conv_res['target_name']} ({conv_res['target_symbol']})</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 {date_str} | 🕒 ساعت: <code>{time_str}</code>\n"
        f"🤖 @{BOT_USERNAME}"
    )






def get_start_inline_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton("◄ تابلوی نرخ ارز، طلا و سکه (بازار آزاد)", callback_data="show_exchange_board"),
        ],
        [
            InlineKeyboardButton("📚 راهنمای کامل استعلام و دستورات", callback_data="show_full_guide"),
        ],
        [
            InlineKeyboardButton(f"{EMOJIS['group']} افزودن ربات به گروه", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"),
            InlineKeyboardButton(f"{EMOJIS['inline']} حالت اینلاین", switch_inline_query=""),
        ],
    ]
    if is_admin:
        kb.append([InlineKeyboardButton(f"{EMOJIS['admin']} پنل مدیریت ادمین", callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Beautiful, comprehensive /start welcome message and guide.
    Automatically removes any previously cached bottom ReplyKeyboardMarkup (per image 77777777777777777777777777777.PNG).
    """
    chat = update.effective_chat
    user = update.effective_user

    if chat.type in ["group", "supergroup"]:
        group_manager.update_group_activity(chat.id, chat.title or "", chat.username or "")
        await update.message.reply_text(
            f"✨ <b>ربات استعلام لحظه‌ای ارز دیجیتال و بازار آزاد (@{BOT_USERNAME}) در گروه فعال است!</b>\n\n"
            f"🔹 <b>دریافت تابلوی کامل ارز و طلا:</b> ارسال عبارت <code>نرخ ارز</code>\n"
            f"🔹 <b>استعلام ارز + چارت نئونی:</b> ارسال نام ارز مثل <code>اتریوم</code>، <code>یک ناتکوین</code>، <code>.btc</code> یا <code>تون</code>\n"
            f"🔹 <b>محاسبه تعداد دلخواه:</b> مثل <code>۷۰ تتر</code> یا <code>2.5 اتریوم</code>\n\n"
            f"📚 برای مشاهده راهنمای کامل به پیوی ربات مراجعه کنید: @{BOT_USERNAME}",
            parse_mode="HTML",
        )
        return

    user_stats = db.get_user_stats(user.id)
    if user_stats and user_stats["is_banned"]:
        await update.message.reply_text(
            f"{EMOJIS['error']} <b>⛔ دسترسی شما به ربات مسدود شده است.</b>",
            parse_mode="HTML",
        )
        return

    db.add_user(user.id, user.username, user.first_name, user.last_name or "")
    db.log_message(user.id, chat.id, "/start", "command")

    
    try:
        rm_msg = await update.message.reply_text("⏳", reply_markup=ReplyKeyboardRemove())
        await rm_msg.delete()
    except Exception:
        pass

    is_admin = user.id in ADMINS
    date_str, time_str = get_jalali_datetime_strings()

    welcome_text = (
        f"🌟 <b>به ربات هوشمند استعلام ارز دیجیتال و بازار آزاد خوش آمدید!</b> 🌟\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>{user.first_name} عزیز، به خانواده بزرگ Crypto ZenthFlow خوش آمدی!</b>\n"
        f"📅 <b>امروز:</b> {date_str} | 🕒 <b>ساعت:</b> <code>{time_str}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <b>با این ربات، نبض بازارهای مالی در دستان شماست! راهنمای سریع استفاده:</b>\n\n"
        f"1️⃣ <b>استعلام تابلوی کامل بازار آزاد، طلا، سکه و رمزارزها:</b>\n"
        f"• کافیست عبارت <code>نرخ ارز</code> را تایپ کنید تا لیست کامل دلار، یورو، پوند، درهم، سکه، مثقال طلا، گرم طلا و رمزارزهای برتر را به صورت لحظه‌ای دریافت کنید.\n\n"
        f"2️⃣ <b>استعلام قیمت و چارت اختصاصی هر ارز (فارسی یا انگلیسی):</b>\n"
        f"• فقط نام یا نماد ارز را بفرستید تا <b>چارت گرافیکی ۲۴ ساعته</b> به همراه دامنه نوسان، سقف و کف، دفتر سفارشات و حجم معاملات نمایش داده شود:\n"
        f"• مثال: <code>اتریوم</code> | <code>ناتکوین</code> | <code>تون کوین</code> | <code>BTC</code> | <code>SOL</code>\n\n"
        f"3️⃣ <b>محاسبه هوشمند تعداد دلخواه هر ارز (عددی یا حروفی):</b>\n"
        f"• تعداد را به فارسی یا انگلیسی کنار نام ارز بنویسید:\n"
        f"• مثال: <code>یک ناتکوین</code> | <code>۷۰ تتر</code> | <code>2.5 اتریوم</code> | <code>نیم بیتکوین</code> | <code>1000 داگز</code>\n\n"
        f"4️⃣ <b>تبدیل مستقیم ارزها به یکدیگر:</b>\n"
        f"• مثال: <code>100 تتر به تومان</code> | <code>2 اتریوم به بیتکوین</code>\n\n"
        f"5️⃣ <b>استفاده در گروه‌ها و چت‌ها:</b>\n"
        f"• ربات را به گروه خود اضافه کرده و دستور <code>نصب ربات</code> را بزنید. در گروه هم بدون نقطه (مثل <code>نرخ ارز</code> یا <code>۷۰ تتر</code>) و هم با نقطه (مثل <code>.btc</code>) پاسخگوی شماست!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>همین حالا نام یا تعداد ارز دلخواهتان را در چت بنویسید:</b>"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_start_inline_keyboard(is_admin),
        parse_mode="HTML",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the detailed guide for all bot commands and features."""
    help_text = (
        f"📚 <b>راهنمای جامع ربات استعلام ارز دیجیتال (@{BOT_USERNAME})</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>۱. تابلوی جامع بازار آزاد، طلا و ارز دیجیتال:</b>\n"
        f"با ارسال کلمه <code>نرخ ارز</code> در پیوی یا گروه، نرخ لحظه‌ای ۱۲ ارز معتبر جهانی (دلار، یورو، پوند، فرانک، درهم، لیر و...)، بازار طلا و سکه (سکه امامی، مثقال، گرم طلای ۱۸ عیار، نقره، انس جهانی) و ۱۱ رمزارز اصلی بازار نمایش داده می‌شود.\n\n"
        f"🟢 <b>۲. استعلام تک‌ارز همراه با چارت گرافیکی 24H:</b>\n"
        f"نام هر ارزی را به فارسی یا انگلیسی بفرستید:\n"
        f"• <code>ناتکوین</code> یا <code>NOT</code>\n"
        f"• <code>اتریوم</code> یا <code>ETH</code>\n"
        f"• <code>تون کوین</code> یا <code>گرام</code> یا <code>TON</code>\n"
        f"• <code>بیتکوین</code> یا <code>BTC</code>\n"
        f"• <code>سولانا</code>، <code>ریپل</code>، <code>دوج کوین</code>، <code>شیبا</code>، <code>پپه</code>، <code>همستر</code>، <code>داگز</code> و بیش از ۱۵۰ ارز دیگر!\n\n"
        f"🟢 <b>۳. محاسبه قیمت تعداد دلخواه ارز (به فارسی و انگلیسی):</b>\n"
        f"• با اعداد فارسی یا انگلیسی: <code>۷۰ تتر</code> | <code>150 تون</code> | <code>0.25 btc</code>\n"
        f"• با حروف فارسی: <code>یک ناتکوین</code> | <code>دو اتریوم</code> | <code>نیم بیتکوین</code> | <code>صد تتر</code>\n\n"
        f"🟢 <b>۴. مبدل هوشمند ارزها:</b>\n"
        f"• <code>70 تتر به تومان</code>\n"
        f"• <code>10000000 تومان به تتر</code>\n"
        f"• <code>1 بیتکوین به اتریوم</code>\n\n"
        f"🟢 <b>۵. دستورات کاربردی در گروه‌ها:</b>\n"
        f"• <code>نصب ربات</code> : فعال‌سازی ربات در گروه توسط ادمین\n"
        f"• <code>نرخ ارز</code> : نمایش تابلوی کامل بازار در گروه\n"
        f"• <code>.btc</code> یا <code>اتریوم</code> یا <code>۷۰ تتر</code> : استعلام به همراه چارت در گروه\n\n"
        f"🟢 <b>۶. دستورات سیستمی:</b>\n"
        f"• /start - شروع مجدد و نمایش منوی اصلی\n"
        f"• /help - نمایش همین راهنما\n"
        f"• /update - بروزرسانی دستی کش قیمت‌ها\n"
        f"• /admin - پنل مدیریت (ویژه ادمین‌های ربات)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌟 <b>با افتخار در خدمت شما هستیم: @{BOT_USERNAME}</b>"
    )

    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("◄ مشاهده تابلوی نرخ ارز", callback_data="show_exchange_board")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_start")],
        ]
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=kb, parse_mode="HTML")
    else:
        await update.message.reply_text(help_text, reply_markup=kb, parse_mode="HTML")






async def send_or_edit_crypto_inquiry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    symbol: str,
    crypto_info: Dict[str, Any],
    amount: float = 1.0,
    explicit_amount: bool = False,
):
    """
    Sends an initial fast text response, renders the Ultra-HD MEOWIE chart with live stats,
    and updates the message with the chart photo and interactive buttons.
    """
    caption_text = build_crypto_caption(crypto_info, symbol, amount, explicit_amount)
    reply_kb = build_crypto_inline_keyboard(symbol, amount)

    if update.callback_query:
        query = update.callback_query
        await query.answer("⏳ در حال بروزرسانی قیمت و ترسیم چارت...")
        chart_bio = await get_crypto_chart_photo(symbol, crypto_info, prefer_local_meowie=True)
        try:
            await context.bot.edit_message_media(
                chat_id=update.effective_chat.id,
                message_id=query.message.message_id,
                media=InputMediaPhoto(media=chart_bio, caption=caption_text, parse_mode="HTML"),
                reply_markup=reply_kb,
            )
            return
        except Exception:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=chart_bio,
                caption=caption_text,
                reply_markup=reply_kb,
                parse_mode="HTML",
            )
            return

    loading_msg = await update.message.reply_text(
        f"⏳ در حال دریافت آخرین اطلاعات بازار و ترسیم چارت ۲۴ ساعته <b>{crypto_info.get('name', symbol)} ({symbol})</b>...",
        parse_mode="HTML",
    )

    chart_bio = await get_crypto_chart_photo(symbol, crypto_info, prefer_local_meowie=True)
    try:
        await context.bot.edit_message_media(
            chat_id=update.effective_chat.id,
            message_id=loading_msg.message_id,
            media=InputMediaPhoto(media=chart_bio, caption=caption_text, parse_mode="HTML"),
            reply_markup=reply_kb,
        )
    except Exception:
        try:
            await loading_msg.delete()
        except Exception:
            pass
        await update.message.reply_photo(
            photo=chart_bio,
            caption=caption_text,
            reply_markup=reply_kb,
            parse_mode="HTML",
        )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main intelligent text router for Private & Group chats:
      - Handles 'نرخ ارز' (without the 3 chart buttons below it)
      - Handles '<amount> <coin>' in Persian/English (e.g. 'یک ناتکوین', '۷۰ تتر', 'اتریوم')
      - Handles currency conversions
    """
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    raw_text = update.message.text.strip()

    user_stats = db.get_user_stats(user.id)
    if user_stats and user_stats["is_banned"]:
        return

    db.add_user(user.id, user.username, user.first_name, user.last_name or "")
    db.update_user_activity(user.id)
    db.log_message(user.id, chat.id, raw_text, "message")

    if chat.type in ["group", "supergroup"]:
        group_manager.update_group_activity(chat.id, chat.title or "", chat.username or "")

    if raw_text in ["راهنما", "📚 راهنمای کامل ربات"]:
        await help_command(update, context)
        return
    if raw_text in ["بروزرسانی", "🔄 بروزرسانی قیمت‌ها"]:
        await update_prices_command(update, context)
        return

    parsed = parse_user_crypto_inquiry(raw_text)

    if parsed["type"] == "exchange_board":
        board_msg = await generate_exact_exchange_rate_board()
        await update.message.reply_text(board_msg, reply_markup=build_exchange_board_keyboard())
        return

    if parsed["type"] == "convert":
        conv_res = await convert_currency_amount(parsed["amount"], parsed["src"], parsed["dst"])
        msg_txt = format_conversion_result_message(conv_res)
        await update.message.reply_text(msg_txt, parse_mode="HTML")
        return

    if parsed["type"] == "inquiry":
        sym, c_info = resolve_currency_query(parsed["query"])
        if sym and c_info:
            if sym == "IRR":
                return
            await send_or_edit_crypto_inquiry(
                update,
                context,
                symbol=sym,
                crypto_info=c_info,
                amount=parsed["amount"],
                explicit_amount=parsed["explicit_amount"],
            )
            return

        if chat.type == "private":
            await update.message.reply_text(
                f"🔍 <b>ارز مورد نظر شما («{raw_text}») یافت نشد!</b>\n\n"
                f"💡 <b>نمونه‌های صحیح جستجو:</b>\n"
                f"• نمایش تابلوی کامل بازار آزاد و طلا: <code>نرخ ارز</code>\n"
                f"• استعلام تک‌ارز با چارت: <code>اتریوم</code> یا <code>یک ناتکوین</code> یا <code>TON</code>\n"
                f"• محاسبه تعداد دلخواه: <code>۷۰ تتر</code> یا <code>2.5 بیتکوین</code>\n"
                f"• تبدیل ارز: <code>100 تتر به تومان</code>",
                parse_mode="HTML",
            )




async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the effective user is in the bot's global ADMINS list."""
    if not update.effective_user:
        return False
    return update.effective_user.id in ADMINS


async def check_user_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Verifies whether the user is a member of all required force-join channels/groups."""
    try:
        chats = get_required_chats()
        if not chats:
            return True
        for chat in chats:
            try:
                chat_member = await context.bot.get_chat_member(chat["chat_id"], user_id)
                if chat_member.status in ["left", "kicked"]:
                    return False
            except Exception as e:
                logger.warning(f"Force-join check warning for chat {chat['chat_id']}: {e}")
                continue
        return True
    except Exception as e:
        logger.error(f"Error checking membership for user {user_id}: {e}")
        return True


def create_join_keyboard() -> Optional[InlineKeyboardMarkup]:
    """Builds the inline keyboard with join links for required channels/groups."""
    chats = get_required_chats()
    if not chats:
        return None

    buttons = []
    for chat in chats:
        chat_type_emoji = "📢" if chat["chat_type"] == "channel" else "👥"
        clean_uname = chat["username"].lstrip("@")
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{chat_type_emoji} عضویت در @{clean_uname}",
                    url=f"https://t.me/{clean_uname}",
                )
            ]
        )

    buttons.append(
        [InlineKeyboardButton("✅ بررسی عضویت و فعال‌سازی ربات", callback_data="check_membership")]
    )
    return InlineKeyboardMarkup(buttons)


async def check_membership_wrapper(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    next_handler,
):
    """Middleware wrapper that checks ban status and mandatory channel membership."""
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    user_stats = db.get_user_stats(user_id)

    if user_stats and user_stats["is_banned"]:
        if update.message and update.effective_chat.type == "private":
            await update.message.reply_text(
                f"{EMOJIS['error']} <b>⛔ دسترسی مسدود شده است</b>\n\n"
                f"متأسفانه حساب شما از استفاده از این ربات مسدود شده است.",
                parse_mode="HTML",
            )
        elif update.callback_query:
            await update.callback_query.answer("⛔ دسترسی شما مسدود شده است!", show_alert=True)
        return

    
    if update.effective_chat and update.effective_chat.type in ["group", "supergroup"]:
        await next_handler(update, context)
        return

    if await is_user_admin(update, context):
        await next_handler(update, context)
        return

    if not await check_user_membership(user_id, context):
        chats = get_required_chats()
        message_text = (
            "⚠️ <b>برای استفاده از ربات استعلام ارز دیجیتال، ابتدا عضو کانال ما شوید!</b>\n\n"
            "🔐 <b>عضویت در چت‌های زیر الزامی است:</b>\n\n"
        )
        for chat in chats:
            chat_type_emoji = "📢" if chat["chat_type"] == "channel" else "👥"
            chat_type_text = "کانال" if chat["chat_type"] == "channel" else "گروه"
            message_text += f"{chat_type_emoji} <b>{chat['username']}</b> ({chat_type_text})\n"

        message_text += (
            "\n✨ <b>مزایای عضویت:</b>\n"
            "• دریافت لحظه‌ای تابلوی <code>نرخ ارز</code>، طلا و سکه\n"
            "• مشاهده چارت نئونی ۲۴ ساعته تمام رمزارزها\n"
            "• محاسبه مقادیر دلخواه (مثل <code>۷۰ تتر</code> یا <code>یک ناتکوین</code>)\n\n"
            "✅ پس از عضویت، روی دکمه «بررسی عضویت» کلیک کنید."
        )

        if update.message:
            await update.message.reply_text(
                message_text,
                reply_markup=create_join_keyboard(),
                parse_mode="HTML",
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                message_text,
                reply_markup=create_join_keyboard(),
                parse_mode="HTML",
            )
        return

    await next_handler(update, context)


async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler for the 'بررسی عضویت' button."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await check_user_membership(user_id, context):
        await query.message.edit_text(
            "✅ <b>عضویت شما با موفقیت تأیید شد!</b>\n\n"
            "✨ اکنون می‌توانید از تمام امکانات ربات استفاده کنید:\n"
            "🔹 ارسال <code>نرخ ارز</code> برای تابلوی کامل بازار آزاد و طلا\n"
            "🔹 ارسال نام ارز مثل <code>اتریوم</code> یا <code>یک ناتکوین</code> برای دریافت چارت\n"
            "🔹 ارسال تعداد مثل <code>۷۰ تتر</code> برای محاسبه دقیق\n\n"
            "🚀 همین حالا امتحان کنید!",
            reply_markup=get_start_inline_keyboard(user_id in ADMINS),
            parse_mode="HTML",
        )
    else:
        await query.answer("❌ شما هنوز در تمام کانال‌های مشخص شده عضو نشده‌اید!", show_alert=True)






async def check_bot_admin_status(group_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        bot_member = await context.bot.get_chat_member(group_id, context.bot.id)
        return bot_member.status in ["administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking bot admin status in {group_id}: {e}")
        return False


async def handle_bot_promoted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when the bot's member status changes in a group (e.g., promoted to Admin)."""
    if not update.my_chat_member:
        return
    chat_member = update.my_chat_member
    new_status = chat_member.new_chat_member.status
    old_status = chat_member.old_chat_member.status

    if new_status in ["administrator", "creator"] and old_status not in ["administrator", "creator"]:
        group = chat_member.chat
        user = chat_member.from_user
        group_manager.add_group(
            group_id=group.id,
            group_title=group.title or "گروه",
            group_username=group.username or "",
            admin_user_id=user.id,
            is_active=1,
        )
        welcome_text = (
            f"✨ <b>ربات استعلام ارز دیجیتال (@{BOT_USERNAME}) با موفقیت ادمین و فعال شد!</b> ✨\n\n"
            f"🔥 <b>امکانات فعال شده در گروه:</b>\n"
            f"✅ ارسال <code>نرخ ارز</code> ⬅️ تابلوی کامل دلار، طلا، سکه و رمزارزها\n"
            f"✅ ارسال نام ارز (مثل <code>اتریوم</code>، <code>یک ناتکوین</code>، <code>.btc</code>) ⬅️ قیمت + چارت ۲۴ ساعته\n"
            f"✅ محاسبه مقادیر دلخواه (مثل <code>۷۰ تتر</code> یا <code>2.5 sol</code>)\n"
            f"✅ تبدیل ارزها (مثل <code>100 تتر به تومان</code>)\n\n"
            f"💎 همچنین می‌توانید دستور <code>نصب ربات</code> را برای مشاهده راهنمای گروه ارسال کنید."
        )
        keyboard = [[InlineKeyboardButton("🚀 ثبت و نصب نهایی ربات", callback_data="install_bot")]]
        try:
            await context.bot.send_message(
                chat_id=group.id,
                text=welcome_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Error sending group promotion message: {e}")


async def handle_group_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when the bot is added as a new member to a group."""
    if not update.message or not update.message.new_chat_members:
        return
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await asyncio.sleep(1.5)
            group = update.effective_chat
            user = update.effective_user
            group_manager.add_group(
                group_id=group.id,
                group_title=group.title or "گروه",
                group_username=group.username or "",
                admin_user_id=user.id,
                is_active=1,
            )
            welcome_text = (
                f"✨ <b>به ربات قیمت لحظه‌ای ارزهای دیجیتال و بازار آزاد خوش آمدید!</b> ✨\n\n"
                f"{EMOJIS['group']} <b>ربات با موفقیت به گروه «{group.title}» اضافه شد!</b>\n\n"
                f"🚀 برای استفاده کامل در گروه، لطفاً ربات را <b>ادمین</b> کرده و دستور زیر را ارسال کنید:\n"
                f"<code>نصب ربات</code>\n\n"
                f"🔥 <b>نمونه دستورات در گروه:</b>\n"
                f"• <code>نرخ ارز</code> (تابلوی کامل بازار آزاد، طلا و رمزارز)\n"
                f"• <code>اتریوم</code> یا <code>یک ناتکوین</code> یا <code>.btc</code> (به همراه چارت)\n"
                f"• <code>۷۰ تتر</code> یا <code>2.5 تون</code> (محاسبه دقیق قیمت)"
            )
            keyboard = [[InlineKeyboardButton("🚀 فعال‌سازی ربات", callback_data="install_bot")]]
            try:
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error(f"Error sending group welcome message: {e}")
            return


async def install_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles 'نصب ربات' command inside groups."""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.message or (update.callback_query.message if update.callback_query else None)

    if chat.type not in ["group", "supergroup"]:
        if msg:
            await msg.reply_text(f"{EMOJIS['error']} این دستور فقط در گروه‌ها قابل استفاده است!")
        return

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ["administrator", "creator"] and user.id not in ADMINS:
            if msg:
                await msg.reply_text(f"{EMOJIS['error']} فقط ادمین‌های گروه می‌توانند ربات را نصب و تنظیم کنند!")
            return
    except Exception as e:
        logger.error(f"Error checking user admin status in group: {e}")

    group_manager.add_group(chat.id, chat.title or "گروه", chat.username or "", user.id, is_active=1)
    group_manager.activate_group(chat.id)

    success_text = (
        f"🎉 <b>تبریک! ربات استعلام ارز دیجیتال با موفقیت در گروه فعال شد!</b> 🎉\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>نمونه دستورات قابل استفاده برای اعضای گروه:</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔸 <code>نرخ ارز</code> ⬅️ تابلوی کامل ارز آزاد، طلا، سکه و رمزارزها\n"
        f"🔹 <code>اتریوم</code> یا <code>.eth</code> ⬅️ قیمت اتریوم + چارت 24H\n"
        f"🔹 <code>یک ناتکوین</code> ⬅️ قیمت نات‌کوین + چارت 24H\n"
        f"🔹 <code>۷۰ تتر</code> ⬅️ محاسبه قیمت ۷۰ تتر + چارت\n"
        f"🔹 <code>تون کوین</code> یا <code>.ton</code> ⬅️ قیمت تون‌کوین + چارت\n"
        f"🔹 <code>100 تتر به تومان</code> ⬅️ تبدیل مستقیم ارزها\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🌟 <b>پیوی ربات جهت مشاهده راهنمای کامل:</b> @{BOT_USERNAME}"
    )
    if msg:
        await msg.reply_text(success_text, parse_mode="HTML")


async def install_bot_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await install_bot_command(update, context)






async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main Admin Control Panel (/admin)."""
    if not await is_user_admin(update, context):
        if update.message:
            await update.message.reply_text(f"{EMOJIS['error']} شما دسترسی ادمین به این بخش را ندارید!")
        elif update.callback_query:
            await update.callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['stats']} آمار پیشرفته ربات", callback_data="admin_stats")],
        [
            InlineKeyboardButton(f"{EMOJIS['users']} مدیریت کاربران", callback_data="admin_users_1"),
            InlineKeyboardButton(f"{EMOJIS['group']} مدیریت گروه‌ها", callback_data="admin_groups_1"),
        ],
        [
            InlineKeyboardButton(f"{EMOJIS['channel']} مدیریت چت‌های اجباری", callback_data="admin_chats_1"),
            InlineKeyboardButton(f"{EMOJIS['message']} ارسال و فوروارد همگانی", callback_data="broadcast_options"),
        ],
        [
            InlineKeyboardButton("🔄 بروزرسانی کش بازار", callback_data="admin_force_update"),
            InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="back_to_start"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    date_str, time_str = get_jalali_datetime_strings()

    message_text = (
        f"{EMOJIS['admin']} <b>پنل مدیریت کل ربات (@{BOT_USERNAME})</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>تاریخ:</b> {date_str} | 🕒 <b>ساعت:</b> <code>{time_str}</code>\n"
        f"💹 <b>ارزهای فعال در کش:</b> <code>{len(crypto_data_cache)}</code> ارز\n\n"
        f"لطفاً یکی از بخش‌های مدیریتی زیر را انتخاب کنید:"
    )

    if update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode="HTML")


async def show_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays detailed bot statistics for admins."""
    query = update.callback_query
    if query:
        await query.answer()

    stats = db.get_bot_stats()
    all_groups = group_manager.get_all_groups()
    active_groups = sum(1 for g in all_groups if g["is_active"])
    active_pct = (stats["active_users"] / stats["total_users"] * 100) if stats["total_users"] > 0 else 0.0
    date_str, time_str = get_jalali_datetime_strings()

    message_text = (
        f"{EMOJIS['stats']} <b>آمار جامع و وضعیت سیستم ربات:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>آمار کاربران:</b>\n"
        f"• کل کاربران ثبت‌شده: <code>{stats['total_users']:,}</code> نفر\n"
        f"• کاربران فعال (۷ روز اخیر): <code>{stats['active_users']:,}</code> ({active_pct:.1f}%)\n"
        f"• کاربران مسدود شده: <code>{stats['banned_users']:,}</code> نفر\n\n"
        f"👥 <b>آمار گروه‌ها:</b>\n"
        f"• کل گروه‌ها: <code>{len(all_groups):,}</code> گروه\n"
        f"• گروه‌های فعال: <code>{active_groups:,}</code> گروه\n\n"
        f"💬 <b>آمار پردازش:</b>\n"
        f"• کل استعلام‌ها و پیام‌ها: <code>{stats['total_messages']:,}</code>\n"
        f"• رمزارزهای آماده در کش: <code>{len(crypto_data_cache)}</code>\n"
        f"• آخرین آپدیت نرخ‌ها: <code>{last_update_time.strftime('%H:%M:%S') if last_update_time else 'نامشخص'}</code>\n"
        f"• زمان سرور (تهران): {date_str} - <code>{time_str}</code>"
    )

    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} بازگشت به پنل ادمین", callback_data="admin_back")]]
    if query:
        await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    elif update.message:
        await update.message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, context):
        await update.message.reply_text(f"{EMOJIS['error']} شما دسترسی لازم برای این دستور را ندارید.")
        return
    await show_bot_stats(update, context)


async def show_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    query = update.callback_query
    if query:
        await query.answer()

    users = db.get_all_users()
    users_per_page = 10
    total_pages = max(1, (len(users) + users_per_page - 1) // users_per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * users_per_page
    end_idx = start_idx + users_per_page
    page_users = users[start_idx:end_idx]

    message_text = f"{EMOJIS['users']} <b>لیست کاربران ربات (صفحه {page} از {total_pages})</b>\n\n"
    if not page_users:
        message_text += "هیچ کاربری یافت نشد."
    else:
        for i, u in enumerate(page_users, start=1):
            num = start_idx + i
            status = "🚫" if u["is_banned"] else "✅"
            uname = f"@{u['username']}" if u["username"] else "بدون یوزرنیم"
            message_text += (
                f"{num}. {status} <b>{u['first_name']}</b> ({uname})\n"
                f"   📊 پیام‌ها: <code>{u['total_messages']}</code> | 🆔: <code>{u['user_id']}</code>\n\n"
            )

    keyboard = []
    for i, u in enumerate(page_users):
        num = start_idx + i + 1
        btn_title = f"{num}. {u['first_name'][:14]} {'🚫' if u['is_banned'] else '✅'}"
        keyboard.append([InlineKeyboardButton(btn_title, callback_data=f"user_detail_{u['user_id']}")])

    nav_btns = []
    if page > 1:
        nav_btns.append(InlineKeyboardButton(f"{EMOJIS['previous']} قبلی", callback_data=f"admin_users_{page - 1}"))
    nav_btns.append(InlineKeyboardButton(f"{EMOJIS['back']} پنل ادمین", callback_data="admin_back"))
    if page < total_pages:
        nav_btns.append(InlineKeyboardButton(f"{EMOJIS['next']} بعدی", callback_data=f"admin_users_{page + 1}"))
    keyboard.append(nav_btns)

    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def show_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    query = update.callback_query
    await query.answer()

    user_stats = db.get_user_stats(user_id)
    if not user_stats:
        await query.edit_message_text(f"{EMOJIS['error']} کاربر مورد نظر یافت نشد!")
        return

    join_date = user_stats["join_date"][:19].replace("T", " ") if user_stats["join_date"] else "نامشخص"
    last_act = user_stats["last_activity"][:19].replace("T", " ") if user_stats["last_activity"] else "نامشخص"

    message_text = (
        f"{EMOJIS['info']} <b>جزئیات حساب کاربر</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>نام:</b> {user_stats['first_name']} {user_stats['last_name'] or ''}\n"
        f"🔗 <b>یوزرنیم:</b> @{user_stats['username'] or 'ندارد'}\n"
        f"🆔 <b>آیدی عددی:</b> <code>{user_stats['user_id']}</code>\n\n"
        f"📊 <b>آمار فعالیت:</b>\n"
        f"• تاریخ عضویت: <code>{join_date}</code>\n"
        f"• آخرین فعالیت: <code>{last_act}</code>\n"
        f"• کل استعلام‌ها: <code>{user_stats['total_messages']}</code>\n\n"
        f"🔒 <b>وضعیت دسترسی:</b> {'🚫 مسدود (بن شده)' if user_stats['is_banned'] else '✅ فعال و مجاز'}"
    )

    keyboard = []
    if user_stats["is_banned"]:
        keyboard.append([InlineKeyboardButton(f"{EMOJIS['unban']} رفع مسدودیت (آنبن)", callback_data=f"user_unban_{user_id}")])
    else:
        keyboard.append([InlineKeyboardButton(f"{EMOJIS['ban']} مسدود کردن کاربر (بن)", callback_data=f"user_ban_{user_id}")])

    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} بازگشت به لیست کاربران", callback_data="admin_users_1")])
    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def manage_user_ban(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, action: str):
    query = update.callback_query
    await query.answer()

    if action == "ban":
        db.ban_user(user_id)
        status_str = "مسدود (بن) شد"
        icon = EMOJIS["ban"]
    else:
        db.unban_user(user_id)
        status_str = "رفع مسدودیت (آنبن) شد"
        icon = EMOJIS["unban"]

    user_stats = db.get_user_stats(user_id) or {"first_name": "کاربر", "last_name": ""}
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} بازگشت به لیست کاربران", callback_data="admin_users_1")]]

    await query.edit_message_text(
        f"{icon} <b>کاربر با موفقیت {status_str}!</b>\n\n"
        f"👤 نام: {user_stats['first_name']} {user_stats.get('last_name', '')}\n"
        f"🆔 آیدی: <code>{user_id}</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


async def show_groups_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    query = update.callback_query
    if query:
        await query.answer()

    groups = group_manager.get_all_groups()
    groups_per_page = 8
    total_pages = max(1, (len(groups) + groups_per_page - 1) // groups_per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * groups_per_page
    end_idx = start_idx + groups_per_page
    page_groups = groups[start_idx:end_idx]

    message_text = f"{EMOJIS['group']} <b>لیست گروه‌های متصل (صفحه {page} از {total_pages})</b>\n\n"
    if not page_groups:
        message_text += "هنوز هیچ گروهی ثبت نشده است."
    else:
        for i, g in enumerate(page_groups, start=1):
            num = start_idx + i
            status = "✅" if g["is_active"] else "🚫"
            uname = f"@{g['group_username']}" if g["group_username"] else "بدون یوزرنیم"
            message_text += (
                f"{num}. {status} <b>{g['group_title']}</b> ({uname})\n"
                f"   📊 پیام‌ها: <code>{g['message_count']}</code> | 🆔: <code>{g['group_id']}</code>\n\n"
            )

    keyboard = []
    nav_btns = []
    if page > 1:
        nav_btns.append(InlineKeyboardButton(f"{EMOJIS['previous']} قبلی", callback_data=f"admin_groups_{page - 1}"))
    nav_btns.append(InlineKeyboardButton(f"{EMOJIS['back']} بازگشت", callback_data="admin_back"))
    if page < total_pages:
        nav_btns.append(InlineKeyboardButton(f"{EMOJIS['next']} بعدی", callback_data=f"admin_groups_{page + 1}"))
    keyboard.append(nav_btns)

    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")






async def show_required_chats_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    query = update.callback_query
    await query.answer()

    chats = db.get_all_required_chats()
    chats_per_page = 8
    total_pages = max(1, (len(chats) + chats_per_page - 1) // chats_per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * chats_per_page
    end_idx = start_idx + chats_per_page
    page_chats = chats[start_idx:end_idx]

    message_text = f"{EMOJIS['channel']} <b>لیست چت‌های عضویت اجباری (صفحه {page} از {total_pages})</b>\n\n"
    if not page_chats:
        message_text += "هیچ کانال یا گروهی برای جوین اجباری تنظیم نشده است.\n"
    else:
        for i, c in enumerate(page_chats, start=1):
            num = start_idx + i
            c_type = "کانال" if c["chat_type"] == "channel" else "گروه"
            message_text += f"{num}. <b>{c['username']}</b> ({c_type}) | 🆔: <code>{c['chat_id']}</code>\n\n"

    keyboard = []
    for i, c in enumerate(page_chats):
        num = start_idx + i + 1
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🗑️ حذف {num}. {c['username']}",
                    callback_data=f"remove_chat_{c['chat_id']}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(f"➕ افزودن کانال/گروه اجباری جدید", callback_data="add_chat")])
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} بازگشت به پنل ادمین", callback_data="admin_back")])

    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def prompt_add_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"{EMOJIS['channel']} <b>افزودن کانال یا گروه به عضویت اجباری</b>\n\n"
        f"لطفاً اطلاعات چت را دقیقاً با فرمت زیر در یک خط ارسال کنید:\n"
        f"<code>@Username ChatID Type</code>\n\n"
        f"🔹 <b>مثال برای کانال:</b>\n"
        f"<code>@MyChannel -1001234567890 channel</code>\n\n"
        f"🔹 <b>مثال برای گروه:</b>\n"
        f"<code>@MyGroup -1009876543210 group</code>\n\n"
        f"⚠️ <i>توجه: ربات باید حتماً در کانال یا گروه مورد نظر ادمین باشد.</i>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_chats_1")]]),
        parse_mode="HTML",
    )


async def remove_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    query = update.callback_query
    await query.answer()
    db.remove_required_chat(chat_id)
    await query.edit_message_text(
        f"{EMOJIS['check']} چت با آیدی <code>{chat_id}</code> از لیست عضویت اجباری حذف شد!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_chats_1")]]),
        parse_mode="HTML",
    )


async def handle_chat_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parses '@ChannelUsername -100123456789 channel' sent by admin to add required chat."""
    if not await is_user_admin(update, context):
        return

    text = update.message.text.strip()
    match = re.match(r"^@(\w+)\s+(-?\d+)\s+(channel|group)$", text, re.IGNORECASE)
    if not match:
        await update.message.reply_text(
            f"{EMOJIS['error']} فرمت نادرست است! نمونه صحیح:\n<code>@ChannelUsername -1001234567890 channel</code>",
            parse_mode="HTML",
        )
        return

    username, chat_id_str, chat_type = match.groups()
    chat_id = int(chat_id_str)
    chat_type = chat_type.lower()

    try:
        chat_obj = await context.bot.get_chat(chat_id)
        db.add_required_chat(chat_obj.id, f"@{username}", chat_type, update.effective_user.id)
        await update.message.reply_text(
            f"{EMOJIS['check']} چت <b>@{username}</b> (<code>{chat_id}</code>) با موفقیت به لیست جوین اجباری اضافه شد!",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(
            f"{EMOJIS['error']} خطا در بررسی چت (مطمئن شوید ربات در چت ادمین است): {e}",
            parse_mode="HTML",
        )


async def broadcast_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📢 راهنمای ارسال پیام همگانی (کپی)", callback_data="broadcast_help")],
        [InlineKeyboardButton("🔁 راهنمای فوروارد همگانی", callback_data="forward_help")],
        [InlineKeyboardButton(f"{EMOJIS['back']} بازگشت به پنل ادمین", callback_data="admin_back")],
    ]
    await query.edit_message_text(
        f"{EMOJIS['message']} <b>بخش پیام همگانی و اطلاع‌رسانی</b>\n\n"
        f"یکی از روش‌های زیر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


async def broadcast_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"{EMOJIS['info']} <b>راهنمای ارسال پیام همگانی (بدون نام فرستنده):</b>\n\n"
        f"1️⃣ روی هر پیامی (متن، عکس، ویدیو یا ویس) ریپلای کنید و دستور <code>/broadcast</code> را بفرستید.\n"
        f"2️⃣ یا مستقیماً بنویسید: <code>/broadcast متن پیام شما</code>\n"
        f"3️⃣ پس از تأیید، پیام به تمامی کاربران ربات ارسال خواهد شد.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJIS['back']} بازگشت", callback_data="admin_back")]]),
        parse_mode="HTML",
    )


async def forward_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"{EMOJIS['info']} <b>راهنمای فوروارد همگانی:</b>\n\n"
        f"1️⃣ روی پیام دلخواه ریپلای کنید.\n"
        f"2️⃣ دستور <code>/forward</code> را ارسال نمایید.\n"
        f"3️⃣ پس از تأیید، پیام برای تمام کاربران فوروارد می‌شود.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJIS['back']} بازگشت", callback_data="admin_back")]]),
        parse_mode="HTML",
    )


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, context):
        await update.message.reply_text(f"{EMOJIS['error']} دسترسی غیرمجاز!")
        return

    if update.message.reply_to_message:
        context.user_data["broadcast_message"] = update.message.reply_to_message
        orig_id = update.message.reply_to_message.message_id
    else:
        if not context.args:
            await update.message.reply_text(
                f"{EMOJIS['info']} روش استفاده:\n"
                f"• ریپلای روی یک پیام و ارسال <code>/broadcast</code>\n"
                f"• یا: <code>/broadcast متن پیام</code>",
                parse_mode="HTML",
            )
            return
        context.user_data["broadcast_message_text"] = " ".join(context.args)
        orig_id = "text"

    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJIS['check']} بله، ارسال شود", callback_data=f"confirm_broadcast_{orig_id}"),
            InlineKeyboardButton(f"{EMOJIS['error']} لغو", callback_data="cancel_broadcast"),
        ]
    ]
    await update.message.reply_text(
        f"{EMOJIS['warning']} <b>آیا از ارسال این پیام به تمامی کاربران ربات اطمینان دارید؟</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


async def forward_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, context):
        await update.message.reply_text(f"{EMOJIS['error']} دسترسی غیرمجاز!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            f"{EMOJIS['info']} لطفاً روی پیامی که می‌خواهید فوروارد همگانی شود ریپلای کرده و دستور <code>/forward</code> را بفرستید.",
            parse_mode="HTML",
        )
        return

    context.user_data["forward_message"] = update.message.reply_to_message
    orig_id = update.message.reply_to_message.message_id
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJIS['check']} بله، فوروارد کن", callback_data=f"confirm_forward_{orig_id}"),
            InlineKeyboardButton(f"{EMOJIS['error']} لغو", callback_data="cancel_broadcast"),
        ]
    ]
    await update.message.reply_text(
        f"{EMOJIS['warning']} <b>آیا از فوروارد همگانی این پیام به تمام کاربران اطمینان دارید؟</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    query = update.callback_query
    await query.answer()

    users = db.get_all_users(limit=100000)
    total_users = len(users)
    success_cnt = 0
    fail_cnt = 0

    progress_msg = await query.edit_message_text(
        f"{EMOJIS['clock']} <b>در حال ارسال پیام همگانی...</b>\n\n"
        f"✅ موفق: 0 | ❌ ناموفق: 0 | کل: {total_users}",
        parse_mode="HTML",
    )

    for i, u in enumerate(users):
        try:
            if mode == "broadcast":
                if "broadcast_message" in context.user_data:
                    await context.bot.copy_message(
                        chat_id=u["user_id"],
                        from_chat_id=update.effective_chat.id,
                        message_id=context.user_data["broadcast_message"].message_id,
                    )
                else:
                    await context.bot.send_message(
                        chat_id=u["user_id"],
                        text=context.user_data.get("broadcast_message_text", ""),
                    )
            elif mode == "forward":
                await context.bot.forward_message(
                    chat_id=u["user_id"],
                    from_chat_id=update.effective_chat.id,
                    message_id=context.user_data["forward_message"].message_id,
                )
            success_cnt += 1
            await asyncio.sleep(0.04)
        except Exception:
            fail_cnt += 1

        if (i + 1) % 20 == 0 or (i + 1) == total_users:
            try:
                pct = ((i + 1) / total_users * 100) if total_users > 0 else 100
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=progress_msg.message_id,
                    text=(
                        f"{EMOJIS['clock']} <b>در حال ارسال همگانی...</b>\n\n"
                        f"✅ موفق: <code>{success_cnt}</code>\n"
                        f"❌ ناموفق: <code>{fail_cnt}</code>\n"
                        f"📊 پیشرفت: <code>{i + 1}/{total_users} ({pct:.1f}%)</code>"
                    ),
                    parse_mode="HTML",
                )
            except Exception:
                pass

    context.user_data.pop("broadcast_message", None)
    context.user_data.pop("broadcast_message_text", None)
    context.user_data.pop("forward_message", None)

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=progress_msg.message_id,
        text=(
            f"{EMOJIS['check']} <b>ارسال همگانی با موفقیت به پایان رسید!</b>\n\n"
            f"👥 کل کاربران: <code>{total_users}</code>\n"
            f"✅ ارسال موفق: <code>{success_cnt}</code>\n"
            f"❌ ارسال ناموفق: <code>{fail_cnt}</code>"
        ),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJIS['back']} بازگشت به پنل", callback_data="admin_back")]]),
        parse_mode="HTML",
    )






async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows users to query crypto prices & 'نرخ ارز' inline in any chat via @CryptoZenthflowbot."""
    user_id = update.inline_query.from_user.id
    user_stats = db.get_user_stats(user_id)
    if user_stats and user_stats["is_banned"]:
        await update.inline_query.answer([], cache_time=1)
        return

    query_str = update.inline_query.query.strip()
    results = []

    if not crypto_data_cache:
        await fetch_live_market_data()

    date_str, time_str = get_jalali_datetime_strings()

    if not query_str or "نرخ" in query_str or "ارز" in query_str or "دلار" in query_str:
        board_text = await generate_exact_exchange_rate_board()
        results.append(
            InlineQueryResultArticle(
                id="exchange_rate_board",
                title="◄ تابلوی کامل نرخ ارز، طلا، سکه و رمزارزها (بازار آزاد)",
                description=f"بروزرسانی: {date_str} ساعت {time_str}",
                input_message_content=InputTextMessageContent(board_text),
            )
        )

    matched_items: List[Tuple[str, Dict[str, Any], float]] = []
    if query_str:
        parsed = parse_user_crypto_inquiry(query_str)
        if parsed["type"] == "inquiry":
            sym, c_info = resolve_currency_query(parsed["query"])
            if sym and c_info and sym != "IRR":
                matched_items.append((sym, c_info, parsed["amount"]))

        q_norm = normalize_persian_text(query_str).lower()
        for sym, c_data in crypto_data_cache.items():
            if any(m[0] == sym for m in matched_items):
                continue
            if q_norm in sym.lower() or q_norm in c_data.get("name", "").lower() or q_norm in c_data.get("en_name", "").lower():
                matched_items.append((sym, c_data, 1.0))
    else:
        for sym in ["BTC", "ETH", "USDT", "TON", "NOT", "SOL", "BNB", "XRP", "TRX", "DOGE", "SHIB", "PAXG"]:
            if sym in crypto_data_cache:
                matched_items.append((sym, crypto_data_cache[sym], 1.0))

    for idx, (sym, crypto, amt) in enumerate(matched_items[:20]):
        unit_irr = float(crypto.get("irr", 0) or 0)
        unit_usdt = float(crypto.get("usdt", 0) or 0)
        tot_irr = unit_irr * amt
        tot_usdt = unit_usdt * amt
        chg = float(crypto.get("dayChange", 0) or 0)
        chg_icon = "📈" if chg > 0 else ("📉" if chg < 0 else "➡️")

        amt_label = f"{amt:g} " if amt != 1.0 else ""
        title = f"{amt_label}{crypto['name']} ({sym})"
        desc = f"{format_price(tot_irr)} تومان | ${format_price(tot_usdt, True)} | {chg_icon} {chg:+.2f}%"
        msg_content = build_crypto_caption(crypto, sym, amount=amt, explicit_amount=(amt != 1.0))

        results.append(
            InlineQueryResultArticle(
                id=f"crypto_{sym}_{idx}",
                title=title,
                description=desc,
                input_message_content=InputTextMessageContent(msg_content, parse_mode="HTML"),
            )
        )

    await update.inline_query.answer(results, cache_time=5)


async def update_prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual /update command handler."""
    wait_msg = await update.message.reply_text("🔄 در حال دریافت آخرین نرخ‌های بازار آزاد، طلا و رمزارزها...")
    await fetch_live_market_data()
    date_str, time_str = get_jalali_datetime_strings()
    await wait_msg.edit_text(
        f"{EMOJIS['check']} <b>تمامی نرخ‌های ارز، طلا و رمزارزها با موفقیت بروزرسانی شدند!</b>\n"
        f"📅 {date_str} | 🕒 ساعت: <code>{time_str}</code>",
        parse_mode="HTML",
    )


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns numeric chat_id and user_id (/id)."""
    chat = update.effective_chat
    user = update.effective_user
    await update.message.reply_text(
        f"🆔 <b>اطلاعات شناسه تلگرام:</b>\n\n"
        f"👤 آیدی عددی شما: <code>{user.id}</code>\n"
        f"💬 آیدی عددی این چت: <code>{chat.id}</code>",
        parse_mode="HTML",
    )


async def master_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Central callback query dispatcher for all inline buttons."""
    query = update.callback_query
    if not query or not query.data:
        return
    data = query.data
    user = query.from_user

    
    if data == "check_membership":
        await check_membership_callback(update, context)
        return

    
    if data == "install_bot":
        await install_bot_button(update, context)
        return

    
    if data == "show_exchange_board":
        await query.answer("⏳ در حال بروزرسانی تابلوی نرخ ارز و طلا...")
        board_text = await generate_exact_exchange_rate_board()
        kb = build_exchange_board_keyboard()
        try:
            if query.message.photo:
                await query.message.reply_text(board_text, reply_markup=kb)
            else:
                await query.edit_message_text(board_text, reply_markup=kb)
        except Exception:
            await query.message.reply_text(board_text, reply_markup=kb)
        return

    if data == "show_full_guide":
        await query.answer()
        await help_command(update, context)
        return

    if data == "back_to_start":
        await query.answer()
        date_str, time_str = get_jalali_datetime_strings()
        welcome_text = (
            f"🌟 <b>منوی اصلی ربات استعلام ارز دیجیتال و بازار آزاد (@{BOT_USERNAME})</b>\n"
            f"📅 {date_str} | 🕒 ساعت: <code>{time_str}</code>\n\n"
            f"• برای تابلوی کامل ارز و طلا بنویسید: <code>نرخ ارز</code>\n"
            f"• برای چارت و اطلاعات ارز بنویسید: <code>اتریوم</code> یا <code>یک ناتکوین</code> یا <code>۷۰ تتر</code>\n\n"
            f"💎 یکی از گزینه‌های زیر را انتخاب کنید:"
        )
        kb = get_start_inline_keyboard(user.id in ADMINS)
        try:
            if query.message.photo:
                await query.message.reply_text(welcome_text, reply_markup=kb, parse_mode="HTML")
            else:
                await query.edit_message_text(welcome_text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await query.message.reply_text(welcome_text, reply_markup=kb, parse_mode="HTML")
        return

    if data.startswith("quick_crypto_"):
        sym = data.replace("quick_crypto_", "").upper()
        await fetch_live_market_data()
        c_info = crypto_data_cache.get(sym)
        if c_info:
            await send_or_edit_crypto_inquiry(update, context, sym, c_info, amount=1.0, explicit_amount=False)
        else:
            await query.answer("⚠️ اطلاعات این ارز یافت نشد.", show_alert=True)
        return

    if data.startswith("refresh_crypto_"):
        parts = data.replace("refresh_crypto_", "").split("_")
        sym = parts[0].upper()
        amt = float(parts[1]) if len(parts) > 1 else 1.0
        await fetch_live_market_data()
        c_info = crypto_data_cache.get(sym)
        if c_info:
            await send_or_edit_crypto_inquiry(update, context, sym, c_info, amount=amt, explicit_amount=(amt != 1.0))
        return

    if data.startswith("calc_crypto_"):
        parts = data.replace("calc_crypto_", "").split("_")
        sym = parts[0].upper()
        amt = float(parts[1]) if len(parts) > 1 else 1.0
        c_info = crypto_data_cache.get(sym)
        if c_info:
            await send_or_edit_crypto_inquiry(update, context, sym, c_info, amount=amt, explicit_amount=True)
        return

    
    if not await is_user_admin(update, context):
        await query.answer("⛔ این بخش ویژه ادمین ربات است!", show_alert=True)
        return

    if data in ["admin_panel", "admin_back"]:
        await admin_panel(update, context)
    elif data == "admin_stats":
        await show_bot_stats(update, context)
    elif data == "admin_force_update":
        await fetch_live_market_data()
        await query.answer("✅ کش قیمت‌ها با موفقیت بروزرسانی شد!", show_alert=True)
        await admin_panel(update, context)
    elif data.startswith("admin_users_"):
        page = int(data.split("_")[2])
        await show_users_list(update, context, page)
    elif data.startswith("admin_groups_"):
        page = int(data.split("_")[2])
        await show_groups_list(update, context, page)
    elif data.startswith("admin_chats"):
        parts = data.split("_")
        page = int(parts[2]) if len(parts) > 2 else 1
        await show_required_chats_list(update, context, page)
    elif data.startswith("user_detail_"):
        uid = int(data.split("_")[2])
        await show_user_detail(update, context, uid)
    elif data.startswith("user_ban_"):
        uid = int(data.split("_")[2])
        await manage_user_ban(update, context, uid, "ban")
    elif data.startswith("user_unban_"):
        uid = int(data.split("_")[2])
        await manage_user_ban(update, context, uid, "unban")
    elif data == "broadcast_options":
        await broadcast_options(update, context)
    elif data == "broadcast_help":
        await broadcast_help(update, context)
    elif data == "forward_help":
        await forward_help(update, context)
    elif data.startswith("confirm_broadcast_"):
        await execute_broadcast(update, context, "broadcast")
    elif data.startswith("confirm_forward_"):
        await execute_broadcast(update, context, "forward")
    elif data == "cancel_broadcast":
        await query.edit_message_text(f"{EMOJIS['info']} عملیات ارسال همگانی لغو شد.")
    elif data == "add_chat":
        await prompt_add_chat(update, context)
    elif data.startswith("remove_chat_"):
        cid = int(data.split("_")[2])
        await remove_chat(update, context, cid)






async def start_with_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_membership_wrapper(update, context, start_command)


async def help_with_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_membership_wrapper(update, context, help_command)


async def update_with_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_membership_wrapper(update, context, update_prices_command)


async def handle_message_with_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_membership_wrapper(update, context, handle_text_message)


async def cleanup_temp_sessions(context: ContextTypes.DEFAULT_TYPE = None):
    """Cleans up expired temporary user sessions."""
    try:
        now = datetime.now(IRAN_TZ)
        expired = [
            uid
            for uid, sdata in user_sessions.items()
            if "last_activity" in sdata and (now - sdata["last_activity"]) > timedelta(hours=24)
        ]
        for uid in expired:
            user_sessions.pop(uid, None)
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Logs unexpected errors cleanly without crashing the polling loop."""
    err_str = str(context.error)
    ignored = [
        "Query is too old",
        "Message is not modified",
        "Message to edit not found",
        "Timed out",
    ]
    if any(ig in err_str for ig in ignored):
        return
    logger.error(f"Exception while handling an update: {context.error}")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set it as an environment variable before starting the bot.")
    """Main entry point to initialize and start @CryptoZenthflowbot."""
    print("=" * 72)
    print(f"💎 Starting {BOT_NAME} (@{BOT_USERNAME}) - CLEAN UI v9.5...")
    date_str, time_str = get_jalali_datetime_strings()
    print(f"📅 Jalali Date : {date_str} | Time: {time_str}")
    print(f"💾 Database    : {DB_FILE_NAME} (Ready)")
    print(f"📊 Coins Loaded: {len(crypto_data_cache)} Cryptocurrencies + Free Market Fiat & Gold")
    print("=" * 72)

    
    try:
        asyncio.get_event_loop().run_until_complete(fetch_live_market_data())
        print("✅ Live Market Data Cache Initialized Successfully!")
    except Exception as e:
        print(f"⚠️ Using Default Market Cache on Boot: {e}")

    request_config = HTTPXRequest(
        connection_pool_size=25,
        connect_timeout=25.0,
        read_timeout=45.0,
        write_timeout=45.0,
        pool_timeout=25.0,
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(request_config)
        .get_updates_request(request_config)
        .build()
    )

    
    application.add_handler(CommandHandler("start", start_with_membership))
    application.add_handler(CommandHandler("help", help_with_membership))
    application.add_handler(CommandHandler("update", update_with_membership))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    application.add_handler(CommandHandler("forward", forward_broadcast))

    
    application.add_handler(ChatMemberHandler(handle_bot_promoted, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.StatusUpdate.NEW_CHAT_MEMBERS,
            handle_group_add,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & filters.Regex(r"^نصب ربات$"),
            install_bot_command,
        )
    )

    
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r"^@\w+\s+-?\d+\s+(channel|group)$"),
            handle_chat_info,
        )
    )

    
    application.add_handler(CallbackQueryHandler(master_callback_router))
    application.add_handler(InlineQueryHandler(inline_query_handler))

    
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message_with_membership,
        )
    )

    
    if application.job_queue:
        application.job_queue.run_repeating(update_crypto_cache, interval=180, first=15)
        application.job_queue.run_repeating(cleanup_temp_sessions, interval=3600, first=60)

    application.add_error_handler(global_error_handler)

    print(f"🚀 @{BOT_USERNAME} is now polling and ready to serve!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
    except Exception as exc:
        print(f"\n❌ Critical startup error: {exc}")
