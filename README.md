🚀 Features

Cryptocurrency Prices: Information about 150+ cryptocurrency assets and tokens.
Live Market Data: Fetch market information from external APIs.
Currency & Gold Rates: Fiat currencies, gold, and silver price information.
Interactive Charts: Generate high-resolution cryptocurrency charts.
Portfolio Manager: Track cryptocurrency holdings.
Price Alerts: Configure price-based notifications.
Smart Calculator: Calculate cryptocurrency quantities and conversions.
Inline Search: Search for cryptocurrency information directly in Telegram.
Admin Panel: User management, statistics, broadcasting, and administration tools.

Persian Language Support: Persian and English cryptocurrency names and queries.

🛠️ Technology Stack
Python 3.10+
python-telegram-bot
SQLite
HTTPX
Requests
Pillow
CoinGecko API
Binance API
Nobitex API
Wallex API

📦 Installation

Clone the repository:

git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY

Install dependencies:

pip install python-telegram-bot pytz httpx requests urllib3 nest_asyncio Pillow

Optional Persian image-rendering dependencies:

pip install arabic-reshaper python-bidi

⚙️ Configuration

Set the following environment variables before starting the bot:

BOT_TOKEN=YOUR_NEW_TELEGRAM_BOT_TOKEN
ADMIN_IDS=123456789,987654321
NOBITEX_FAST_API=YOUR_COMPLETE_NOBITEX_API_URL
FAST_CHART_API=YOUR_COMPLETE_CHART_API_URL

▶️ Run
python crypto_zenthflow_bot_github.py

🔐 Security
Credentials are loaded through environment variables.


👨‍💻 Project

Crypto ZenthFlow Bot
Telegram: @CryptoZenthflowbot
