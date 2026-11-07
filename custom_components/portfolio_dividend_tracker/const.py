DOMAIN = "portfolio_dividend_tracker"
API_URL = "https://api.portfoliodividendtracker.com/v1/portfolio"
BASE_URL = "https://api.portfoliodividendtracker.com/v1"
UPDATE_INTERVAL_MINUTES = 15
ALLOWED_RESOURCES = (
    "portfolio", "transactions", "dividends", "bookings", "expenses",
    "investment-strategies", "symbols", "prices", "brokers",
    "calendar-events", "exchange-rates", "changelog",
)
