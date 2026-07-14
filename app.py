import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit.components.v1 as components
import google.generativeai as genai
import feedparser
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from gemini_config import ai_model
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from gemini_config import ai_model
from streamlit_autorefresh import st_autorefresh
from yahooquery import search

st.write("AI GLOBAL TRADING PATFORM")


# PAGE CONFIG


st.set_page_config(
    page_title="AI Global Trading Platform",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>

.stApp{
    background:#0E1117;
}

h1,h2,h3{
    color:white;
}

div[data-testid="metric-container"]{
    background:#1f2937;
    padding:18px;
    border-radius:15px;
    border:1px solid #333;
    box-shadow:0px 3px 8px rgba(0,0,0,.35);
}

div[data-testid="metric-container"]:hover{
    transform:scale(1.03);
    transition:.3s;
}

</style>
""", unsafe_allow_html=True)

# AUTO REFRESH

st_autorefresh(
    interval=90000,
    key="market_refresh"
)


# TITLE

st.title(" AI Global Trading Platform")

st.markdown("""
## Real-Time AI Trading, Prediction & Learning Platform
""")

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header(" Market Settings")

market = st.sidebar.selectbox(

    "Select Market",

    [
        "Indian Stocks",
        "US Stocks",
        "Crypto"
    ]
)

stock_input = st.sidebar.text_input(
    "Search Stock",
    "INFY"
)

# =========================================================
# =========================================================
# PROFESSIONAL SYMBOL DETECTION
# =========================================================

def get_stock_symbol(company_name, market):
    try:
        result = search(company_name)

        if result and "quotes" in result:

            for item in result["quotes"]:

                symbol = item.get("symbol", "")

                exchange = item.get("exchange", "")

                # Indian Stocks
                if market == "Indian Stocks":
                    if symbol.endswith(".NS"):
                        return symbol

                # US Stocks
                elif market == "US Stocks":
                    if not symbol.endswith(".NS"):
                        return symbol

        return company_name

    except:
        return company_name


if market == "Indian Stocks":

    stock = get_stock_symbol(stock_input, market)

    if not stock.endswith(".NS"):
        stock = f"{stock}.NS"

    trading_symbol = f"NSE:{stock.replace('.NS','')}"

elif market == "US Stocks":

    stock = get_stock_symbol(stock_input, market)

    trading_symbol = f"NASDAQ:{stock}"

else:

    stock = stock_input.upper()

    if not stock.endswith("-USD"):
        stock = f"{stock}-USD"

    trading_symbol = f"BINANCE:{stock.replace('-USD','')}USDT"


st.sidebar.success(f"Selected Stock: {stock}")
# =========================================================
# LIVE MARKET DATA
# =========================================================

data = yf.download(
    stock,
    period="5d",
    interval="1m",
    progress=False
)
if data.empty:
    st.error("No live market data found.")
    st.stop()
# =========================================================
# HISTORICAL TRAINING DATA
# =========================================================

train_data = yf.download(

    stock,

    period="2y",

    interval="1d",

    progress=False
)

# =========================================================
# FIX MULTI INDEX
# =========================================================

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

if isinstance(train_data.columns, pd.MultiIndex):
    train_data.columns = train_data.columns.get_level_values(0)

# =========================================================
# CHECK DATA
# =========================================================

if data.empty:

    st.error("No stock data found")

    st.stop()
# =========================================================
# COMPANY INFORMATION
# =========================================================

ticker = yf.Ticker(stock)

try:

    info = ticker.info

    company = info.get("longName", stock)
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    website = info.get("website", "N/A")
    country = info.get("country", "N/A")

    st.markdown(f"""
    <div style="background:#1b263b;padding:20px;border
    radius:15px;border:1px solid #3a506b;">
    <h2> {company}</h2>
    <b>Sector:</b> {sector}<br>
    <b>Industry:</b> {industry}<br>
    <b>Country:</b> {country}<br>
    <b>Website:</b> <a href="{website}" target="_blank">{website}</a>
    </div>
    """, unsafe_allow_html=True)

except:

    st.subheader(stock)
# =========================================================
# LIVE METRICS
# =========================================================

latest_price = data['Close'].iloc[-1]

high_price = data['High'].max()

low_price = data['Low'].min()

volume = data['Volume'].iloc[-1]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Current Price",
    f"{latest_price:.2f}"
)

col2.metric(
    "Day High",
    f"{high_price:.2f}"
)

col3.metric(
    "Day Low",
    f"{low_price:.2f}"
)

col4.metric(
    "Volume",
    f"{volume:,}"
)

# =========================================================
# LIVE PRICE CHART
# =========================================================

st.subheader(" Live Share Price")

st.line_chart(data['Close'])

# =========================================================
# LIVE CANDLESTICK CHART
# =========================================================

st.subheader(" Real-Time Candlestick Chart")

fig = go.Figure(data=[go.Candlestick(

    x=data.index,

    open=data['Open'],

    high=data['High'],

    low=data['Low'],

    close=data['Close']

)])

fig.update_layout(

    height=600,

    xaxis_rangeslider_visible=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================================

# LIVE TRADINGVIEW CHART
# =========================================================
container_id = f"tv_chart_{market}_{stock}"
tradingview_widget = f"""
<div class="tradingview-widget-container" style="height:1000px;">
  <div id="{container_id}"style="height:100%; width:100%;"></div>

  <script type="text/javascript"
  src="https://s3.tradingview.com/tv.js"></script>

  <script type="text/javascript">

  new TradingView.widget(
  {{
    "width": "100%",
    "height": 950,
    "symbol": "{trading_symbol}",
    "interval": "5",
    "timezone": "Asia/Kolkata",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#131722",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "save_image": true,
    "withdateranges": true,
    "hide_side_toolbar": false,
    "studies": [
      "RSI@tv-basicstudies",
      "MACD@tv-basicstudies"
    ],
    "container_id": "{container_id}"
  }});

  </script>
</div>
"""

components.html(
    tradingview_widget,
    height=1000,
    scrolling=True
)
# =========================================================
# TECHNICAL INDICATORS
# =========================================================

st.subheader(" Technical Indicators")

# RSI

rsi = RSIIndicator(
    close=train_data['Close']
)

train_data['RSI'] = rsi.rsi()

# MACD

macd = MACD(
    close=train_data['Close']
)

train_data['MACD'] = macd.macd()

# MOVING AVERAGE

train_data['MA20'] = (
    train_data['Close']
    .rolling(20)
    .mean()
)

train_data['MA50'] = (
    train_data['Close']
    .rolling(50)
    .mean()
)

# BOLLINGER BANDS

bb = BollingerBands(
    close=train_data['Close']
)

train_data['BB_High'] = bb.bollinger_hband()

train_data['BB_Low'] = bb.bollinger_lband()

train_data = train_data.dropna()

# =========================================================
# EXTRA FEATURES FOR BETTER ACCURACY
# =========================================================

train_data['Returns'] = train_data['Close'].pct_change()

train_data['Volatility'] = (
    train_data['Returns']
    .rolling(20)
    .std()
)

train_data['EMA20'] = (
    train_data['Close']
    .ewm(span=20)
    .mean()
)

train_data['EMA50'] = (
    train_data['Close']
    .ewm(span=50)
    .mean()
)

# Remove NaN values created by indicators
train_data = train_data.dropna()


# RSI CHART

st.write("### RSI Indicator")

st.line_chart(
    train_data['RSI']
)

# MACD CHART

st.write("### MACD Indicator")

st.line_chart(
    train_data['MACD']
)

# =========================================================
# CANDLESTICK PATTERN DETECTION
# =========================================================

st.subheader(" Candlestick Pattern Detection")

if len(train_data) < 2:
    st.warning("Not enough data")
else:

    latest = train_data.iloc[-1]
    prev = train_data.iloc[-2]

    body = abs(
        latest['Close'] - latest['Open']
    )

    range_size = (
        latest['High'] - latest['Low']
    )

    lower_shadow = (
        min(
            latest['Open'],
            latest['Close']
        ) - latest['Low']
    )

    upper_shadow = (
        latest['High']
        - max(
            latest['Open'],
            latest['Close']
        )
    )

    pattern_message = "No Pattern"

    # --------------------
    # Doji
    # --------------------

    if body <= range_size * 0.1:

        pattern_message = "Doji"

        st.info(
            " Doji Pattern Detected"
        )

    # --------------------
    # Hammer
    # --------------------

    elif (
        lower_shadow > body * 2
        and upper_shadow < body * 0.5
    ):

        pattern_message = "Hammer"

        st.success(
            " Hammer Pattern Detected"
        )

    # --------------------
    # Bullish Engulfing
    # --------------------

    elif (

        prev['Close'] < prev['Open']

        and latest['Close'] > latest['Open']

        and latest['Open'] < prev['Close']

        and latest['Close'] > prev['Open']

    ):

        pattern_message = "Bullish Engulfing"

        st.success(
            " Bullish Engulfing Detected"
        )

    # --------------------
    # Bearish Engulfing
    # --------------------

    elif (

        prev['Close'] > prev['Open']

        and latest['Close'] < latest['Open']

        and latest['Open'] > prev['Close']

        and latest['Close'] < prev['Open']

    ):

        pattern_message = "Bearish Engulfing"

        st.error(
            " Bearish Engulfing Detected"
        )

    # --------------------
    # Bullish/Bearish Candle
    # --------------------

    if latest['Close'] > latest['Open']:
        candle_type = "Bullish"

    else:
        candle_type = "Bearish"

    st.write(
        f"### Pattern: {pattern_message}"
    )

    st.write(
        f"### Candle Type: {candle_type}"
    )

    # --------------------
    # Recommendation
    # --------------------

    if pattern_message in [
        "Hammer",
        "Bullish Engulfing"
    ]:

        st.success(
            " BUY SIGNAL"
        )

    elif pattern_message == "Bearish Engulfing":

        st.error(
            " SELL SIGNAL"
        )

    elif pattern_message == "Doji":

        st.warning(
            " Wait For Confirmation"
        )

    else:

        st.info(
            "No Strong Pattern Found"
        )
# =========================================================
# AI MACHINE LEARNING MODEL
# =========================================================

st.subheader(" AI Stock Prediction")

train_data['Prediction'] = (
    train_data['Close'].shift(-1)
)

train_data = train_data.dropna()

features = [

    'Open',
    'High',
    'Low',
    'Close',
    'Volume',

    'RSI',
    'MACD',

    'MA20',
    'MA50',

    'EMA20',
    'EMA50',

    'Returns',
    'Volatility',

    'BB_High',
    'BB_Low'
]

X = np.array(
    train_data[features]
)

Y = np.array(
    train_data['Prediction']
)

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error
)

# =========================================================
# TIME SERIES VALIDATION
# =========================================================

tscv = TimeSeriesSplit(n_splits=5)

r2_scores = []

for train_index, test_index in tscv.split(X):

    X_train = X[train_index]
    X_test = X[test_index]

    y_train = Y[train_index]
    y_test = Y[test_index]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    r2_scores.append(
        r2_score(y_test, predictions)
    )

# =========================================================
# FINAL METRICS
# =========================================================

r2 = r2_score(y_test, predictions)

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        predictions
    )
)

c1, c2, c3 = st.columns(3)

c1.metric("R² Score", round(r2, 4))
c2.metric("MAE", round(mae, 2))
c3.metric("RMSE", round(rmse, 2))

st.success(
    f"Average Validation Score: {np.mean(r2_scores):.4f}"
)
# =========================================================
# FINAL MODEL FOR LIVE PREDICTION
# =========================================================

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42
)

model.fit(X, Y)
# =========================================================
# LIVE AI PREDICTION
# =========================================================

latest_features = np.array([[
    train_data['Open'].iloc[-1],
    train_data['High'].iloc[-1],
    train_data['Low'].iloc[-1],
    train_data['Close'].iloc[-1],
    train_data['Volume'].iloc[-1],

    train_data['RSI'].iloc[-1],
    train_data['MACD'].iloc[-1],

    train_data['MA20'].iloc[-1],
    train_data['MA50'].iloc[-1],

    train_data['EMA20'].iloc[-1],
    train_data['EMA50'].iloc[-1],

    train_data['Returns'].iloc[-1],
    train_data['Volatility'].iloc[-1],

    train_data['BB_High'].iloc[-1],
    train_data['BB_Low'].iloc[-1]
]])

predicted_price = model.predict(
    latest_features
)[0]

# PREVENT UNREALISTIC PRICES

predicted_price = np.clip(

    predicted_price,

    latest_price * 0.95,

    latest_price * 1.05
)

# =========================================================
# PREDICTION DATAFRAME
# =========================================================

future_df = pd.DataFrame({

    "Current Price": [latest_price],

    "Predicted Price": [predicted_price]
})

st.dataframe(future_df)

# =========================================================
# PREDICTION GRAPH
# =========================================================

st.subheader(" AI Prediction Graph")

prediction_fig = go.Figure()

prediction_fig.add_trace(go.Bar(

    x=["Current Price"],

    y=[latest_price],

    name="Current Price"
))

prediction_fig.add_trace(go.Bar(

    x=["Predicted Price"],

    y=[predicted_price],

    name="Predicted Price"
))

prediction_fig.update_layout(
    height=500
)

st.plotly_chart(
    prediction_fig,
    use_container_width=True
)

# =========================================================
# ADVANCED AI BUY SELL SIGNAL
# =========================================================

st.subheader(" AI Trading Signal")

change_percent = (
    (predicted_price - latest_price)
    / latest_price
) * 100

# Latest Indicator Values

current_rsi = train_data['RSI'].iloc[-1]
current_macd = train_data['MACD'].iloc[-1]

current_ma20 = train_data['MA20'].iloc[-1]
current_ma50 = train_data['MA50'].iloc[-1]

signal_score = 0

# ---------------------------------
# Prediction Signal
# ---------------------------------

if predicted_price > latest_price:
    signal_score += 1
else:
    signal_score -= 1

# ---------------------------------
# RSI Signal
# ---------------------------------

if current_rsi < 30:
    signal_score += 1

elif current_rsi > 70:
    signal_score -= 1

# ---------------------------------
# MACD Signal
# ---------------------------------

if current_macd > 0:
    signal_score += 1
else:
    signal_score -= 1

# ---------------------------------
# Moving Average Trend
# ---------------------------------

if current_ma20 > current_ma50:
    signal_score += 1
else:
    signal_score -= 1

# ---------------------------------
# Final Recommendation
# ---------------------------------

if signal_score >= 3:
    recommendation = "STRONG BUY"

elif signal_score >= 1:
    recommendation = "BUY"

elif signal_score <= -3:
    recommendation = "STRONG SELL"

elif signal_score <= -1:
    recommendation = "SELL"

else:
    recommendation = "HOLD"

# ---------------------------------
# Display Signal
# ---------------------------------

st.write(f"Expected Change: {change_percent:.2f}%")
st.write(f"Signal Score: {signal_score}/4")

if recommendation == "STRONG BUY":
    st.success(" STRONG BUY SIGNAL")

elif recommendation == "BUY":
    st.success(" BUY SIGNAL")

elif recommendation == "STRONG SELL":
    st.error(" STRONG SELL SIGNAL")

elif recommendation == "SELL":
    st.error(" SELL SIGNAL")

else:
    st.warning(" HOLD SIGNAL")

# ---------------------------------
# Confidence
# ---------------------------------

confidence = (abs(signal_score) / 4) * 100

st.metric(
    "Prediction Confidence",
    f"{confidence:.0f}%"
)

# ---------------------------------
# Trade Setup
# ---------------------------------

entry_price = latest_price

target_price = predicted_price

stop_loss = latest_price * 0.97

st.write("###  Trade Setup")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Entry Price",
    f"{entry_price:.2f}"
)

c2.metric(
    "Target Price",
    f"{target_price:.2f}"
)

c3.metric(
    "Stop Loss",
    f"{stop_loss:.2f}"
)

# ---------------------------------
# Indicator Summary
# ---------------------------------

summary = pd.DataFrame({
    "Indicator": ["RSI", "MACD", "MA Trend"],
    "Value": [
        round(current_rsi, 2),
        round(current_macd, 2),
        "Bullish" if current_ma20 > current_ma50 else "Bearish"
    ]
})

st.dataframe(summary)

# =========================================================
# LLM AI MARKET ANALYST
# =========================================================

st.header(" AI Market Analyst")

if st.button("Generate AI Analysis"):

    with st.spinner("Analyzing market using AI..."):

        analysis_prompt = f"""
You are an expert financial analyst.

Analyze this stock using the information below.

Stock Symbol:
{stock}

Current Price:
{latest_price:.2f}

Predicted Price:
{predicted_price:.2f}

Prediction Change:
{change_percent:.2f}%

Recommendation:
{recommendation}

Confidence:
{confidence:.2f}%

Technical Indicators

RSI:
{current_rsi:.2f}

MACD:
{current_macd:.2f}

20 Moving Average:
{current_ma20:.2f}

50 Moving Average:
{current_ma50:.2f}

Provide:

1. Market Trend
2. Technical Analysis
3. Investment Recommendation
4. Risk Level
5. Entry Price
6. Target Price
7. Stop Loss
8. Beginner Explanation
9. Long Term Outlook
10. Short Term Outlook

Explain in professional language.
"""

        response = ai_model.generate_content(analysis_prompt)

        st.success("Analysis Complete")

        st.markdown(response.text)

# =========================================================
# AI STOCK CHATBOT
# =========================================================

st.header(" AI Stock Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_question = st.chat_input(
    "Ask about this stock..."
)

if user_question:

    with st.chat_message("user"):
        st.markdown(user_question)

    st.session_state.messages.append(
        {"role": "user", "content": user_question}
    )

    prompt = f"""
    You are a professional stock market analyst.

    Stock: {stock}

    Current Price: {latest_price}

    Predicted Price: {predicted_price}

    RSI: {train_data['RSI'].iloc[-1]}

    MACD: {train_data['MACD'].iloc[-1]}

    Expected Change: {change_percent:.2f}%

    Answer the user's question.

    Also provide:
    1. Trend
    2. Buy/Sell/Hold
    3. Risk Level
    4. Entry Price
    5. Target Price
    6. Stop Loss
    7. Beginner Explanation

    User Question:
    {user_question}
    """

    with st.spinner("AI analyzing..."):

        response = ai_model.generate_content(prompt)

        ai_reply = response.text

        st.session_state.messages.append(
            {"role": "assistant", "content": ai_reply}
        )

        with st.chat_message("assistant"):
            st.markdown(ai_reply)
# =========================================================
# =========================================================
# ADVANCED PORTFOLIO TRACKER
# =========================================================

st.subheader(" Smart Portfolio Tracker")

# Session Storage

if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# ==========================================
# ADD STOCK FORM
# ==========================================

st.write("### Add Stock")

col1, col2, col3 = st.columns(3)

with col1:
    portfolio_stock = st.text_input(
        "Stock Symbol",
        "INFY.NS"
    )

with col2:
    portfolio_qty = st.number_input(
        "Quantity",
        min_value=1,
        value=1
    )

with col3:
    buy_price = st.number_input(
        "Buy Price",
        min_value=0.0,
        value=100.0
    )

if st.button(" Add To Portfolio"):

    st.session_state.portfolio.append({

        "Stock": portfolio_stock.upper(),

        "Quantity": portfolio_qty,

        "Buy Price": buy_price

    })

    st.success("Stock Added Successfully")

# ==========================================
# PORTFOLIO TABLE
# ==========================================

portfolio_data = []

for item in st.session_state.portfolio:

    symbol = item["Stock"]
    qty = item["Quantity"]
    buy_price = item["Buy Price"]

    try:

        stock_data = yf.Ticker(symbol)

        hist = stock_data.history(period="1d")

        if hist.empty:
            continue

        current_price = hist["Close"].iloc[-1]

        investment = buy_price * qty

        current_value = current_price * qty

        profit_loss = current_value - investment

        # Recommendation Logic

        recommendation = "HOLD"

        if current_price > buy_price * 1.05:
            recommendation = "SELL"

        elif current_price < buy_price * 0.95:
            recommendation = "BUY"

        portfolio_data.append({

            "Stock": symbol,

            "Quantity": qty,

            "Buy Price": round(buy_price, 2),

            "Current Price": round(current_price, 2),

            "Recommendation": recommendation,

            "Investment": round(investment, 2),

            "Current Value": round(current_value, 2),

            "Profit/Loss": round(profit_loss, 2)

        })

    except Exception as e:
        pass

portfolio_df = pd.DataFrame(portfolio_data)
# ==========================================
# PORTFOLIO TABLE
# ==========================================

portfolio_data = []

for item in st.session_state.portfolio:

    symbol = item["Stock"]

    qty = item["Quantity"]

    buy_price = item["Buy Price"]

    try:

        stock_data = yf.Ticker(symbol)

        hist = stock_data.history(period="1d")

        current_price = hist["Close"].iloc[-1]

        investment = buy_price * qty

        current_value = current_price * qty

        profit_loss = current_value - investment

        portfolio_data.append({

            "Stock": symbol,

            "Quantity": qty,

            "Buy Price": round(buy_price, 2),

            "Current Price": round(current_price, 2),

            "Investment": round(investment, 2),

            "Current Value": round(current_value, 2),

            "Recommendation": recommendation,

            "Profit/Loss": round(profit_loss, 2)

        })

    except:
        pass

portfolio_df = pd.DataFrame(portfolio_data)

# ==========================================
# SHOW DATAFRAME
# ==========================================

if not portfolio_df.empty:

    st.dataframe(
        portfolio_df,
        use_container_width=True
    )

    # ======================================
    # SUMMARY METRICS
    # ======================================

    total_investment = portfolio_df["Investment"].sum()

    total_value = portfolio_df["Current Value"].sum()

    total_profit = portfolio_df["Profit/Loss"].sum()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Investment",
        f"₹{total_investment:,.2f}"
    )

    c2.metric(
        "Current Value",
        f"₹{total_value:,.2f}"
    )

    c3.metric(
        "Profit / Loss",
        f"₹{total_profit:,.2f}"
    )

    # ======================================
    # PIE CHART
    # ======================================

    st.write("### Portfolio Allocation")

    pie_fig = go.Figure(

        data=[

            go.Pie(

                labels=portfolio_df["Stock"],

                values=portfolio_df["Current Value"],

                hole=0.4
            )
        ]
    )

    pie_fig.update_layout(
        height=500
    )

    st.plotly_chart(
        pie_fig,
        use_container_width=True
    )

else:

    st.info(
        "Add stocks to build your portfolio."
    )


st.header("📊 AI Portfolio Advisor")

if st.button("Analyze My Portfolio"):

    portfolio_text = portfolio_df.to_string(index=False)

    prompt = f"""
    You are a portfolio manager.
    Analyze this portfolio.
    {portfolio_text}
    Provide:
    1. Diversification Score
    2. Portfolio Risk
    3. Weak Stocks
    4. Strong Stocks
    5. Sector Allocation
    6. Improvement Suggestions
    7. Which stock should be bought next?
    """

    response = ai_model.generate_content(prompt)

    st.markdown(response.text)  

# =========================================================
# LEARNING PLATFORM
# =========================================================

st.header(" Learn Share Market")

topic = st.selectbox(

    "Choose Topic",

    [
        "Bull Market",
        "Bear Market",
        "RSI",
        "MACD",
        "Candlestick",
        "Risk Management"
    ]
)

learning_content = {

    "Bull Market":
    "Bull market means stock prices are rising continuously.",

    "Bear Market":
    "Bear market means stock prices are falling continuously.",

    "RSI":
    "RSI measures stock momentum. Above 70 means overbought and below 30 means oversold.",

    "MACD":
    "MACD helps identify trend direction and momentum.",

    "Candlestick":
    "Candlestick charts show Open, High, Low and Close prices.",

    "Risk Management":
    "Risk management helps reduce trading losses."
}

st.info(
    learning_content[topic]
)
st.header(" AI Stock Market Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask anything about the stock market...")

if prompt:

    st.session_state.messages.append(
        {"role":"user","content":prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    response = ai_model.generate_content(prompt)

    answer = response.text

    st.session_state.messages.append(
        {"role":"assistant","content":answer}
    )

    with st.chat_message("assistant"):
        st.markdown(answer)
# =========================================================
# DISCLAIMER
# =========================================================

st.warning("""

This platform is for educational purposes only.

Stock market investments involve risk.

AI predictions are not guaranteed.

""")