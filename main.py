import requests
from datetime import date, timedelta
from twilio.rest import Client
import pandas
import time
import os
ALPHAVANTAGE_API_KEI = os.environ.get("ALPHAVANTAGE_API_KEI")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
ACCOUNT_SID = os.environ.get("ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
MY_PHONE_NUMBER = os.environ.get("MY_PHONE_NUMBER")
MY_TRIAL_PHONE_NUMBER = os.environ.get("MY_TRIAL_PHONE_NUMBER")
DELTA = 5

# Check if stock's price changed above delta
def check_stock_change(stock, company):
    parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": stock,
        "apikey": ALPHAVANTAGE_API_KEI,
    }

    response = requests.get(
        "https://www.alphavantage.co/query",
        params=parameters
    )
    response.raise_for_status()

    data = response.json()
    print(data)

    # Handle Alpha Vantage rate limit / errors
    if "Time Series (Daily)" not in data:
        print("Alpha Vantage API error:")
        print(data)
        return None

    series = data["Time Series (Daily)"]

    dates = list(series.keys())

    # Most recent trading day
    today_key = dates[0]

    # Previous trading day
    yesterday_key = dates[1]

    today_info = series[today_key]
    yesterday_info = series[yesterday_key]

    today_open = float(today_info["1. open"])
    yesterday_close = float(yesterday_info["4. close"])

    delta = ((today_open - yesterday_close) / yesterday_close) * 100

    return round(delta, 2)


# Get the first 3 news pieces for the company.
def get_company_news(company):
    print(f"Getting news for {company}")
    yesterday = date.today() - timedelta(days=1)
    parameters = {
        "q": company,
        "language": "en",
        "pageSize": 3,
        "apiKey": NEWS_API_KEY
    }

    response = requests.get("https://newsapi.org/v2/everything", params=parameters)
    response.raise_for_status()
    data = response.json()

    res = {}
    for article in data["articles"]:
        res[article["title"]] = article["description"]
    return res


# Send message with the percentage change and each article's title and description.
def send_text_message(company, delta, articles):
    print(f"Sending text message for {company}")
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    body = f"{company.upper()}: {delta * 100}%\n"
    for article in articles:
        body += f"Headline: {article}\nBrief: {articles[article]}\n\n"

    message = client.messages.create(
        body=body,
        from_=MY_TRIAL_PHONE_NUMBER,
        to=MY_PHONE_NUMBER,
    )
    print(message.status)

df = pandas.read_csv("stocks.csv")
for index, row in df.iterrows():

    STOCK = row.ticker
    COMPANY_NAME = row.company

    delta = check_stock_change(STOCK, COMPANY_NAME)

    if delta is None:
        continue

    if abs(delta) >= DELTA:
        articles = get_company_news(COMPANY_NAME)
        send_text_message(COMPANY_NAME, delta, articles)

    # Have to avoid API throttling
    time.sleep(12)


