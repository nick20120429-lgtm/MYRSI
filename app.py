import os
import urllib.parse
import pandas as pd
import streamlit as st
import yfinance as yf
import feedparser
from google import genai

st.set_page_config(page_title="犀利媽 20年極端心法分析工具", page_icon="📈", layout="wide")

# 頂部開發者資訊與圖片展示區塊
col_img, col_header = st.columns([1, 4])

with col_img:
    image_path = "avatar.png"
    if os.path.exists(image_path):
        st.image(image_path, width=110)

with col_header:
    st.markdown("**開發者：尼克范 2026.10.21.V17（字串串接終極穩健版）**")
    st.title("📈 犀利媽 20年極端心法與即時新聞動態分析工具")

st.write("本工具**支援全台灣上市櫃股票**。請輸入台股代號（例如：2330、6239、3231、2317）：")
st.write(
    "💡 **犀利媽 20年核心哲學**：「常態區間不看雜訊、極端行情絕不手軟、對照消息面靈活操作、破支撐手刀停損！」"
)

# 自動背景讀取 API Key
gemini_api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

stock_name_dict = {
    "2330": "台積電",
    "6239": "力成",
    "2317": "鴻海",
    "3605": "宏致",
    "5347": "世界",
    "3231": "緯創",
    "2454": "聯發科",
    "2308": "台達電",
    "2382": "廣達",
    "3037": "欣興",
}

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def fetch_stock_news(stock_code, stock_name, count=10):
    search_query = f"{stock_code} {stock_name}" if stock_name != "台股公司" else stock_code
    encoded_query = urllib.parse.quote(search_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}+when:30d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    if feed.entries:
        for entry in feed.entries[:count]:
            pub_date = getattr(entry, "published", "")[:16] if hasattr(entry, "published"] else ""
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "date": pub_date,
                "source": entry.source.title if hasattr(entry, "source") else "財經新聞"
            })
    return news_items

col_input, col_btn = st.columns([3, 1])

with col_input:
    stock_input = st.text_input(
        "請輸入台股代號（例如 6239）：", value="6239", label_visibility="collapsed"
    )

with col_btn:
    st.write("")
    submit_btn = st.button("確定查詢", type="primary")

if submit_btn and stock_input:
    raw_input = stock_input.strip()
    stock_digits = "".join(filter(str.isdigit, raw_input))

    if not stock_digits:
        st.error("請輸入正確的台股數字代號（例如：2330、6239）！")
    else:
        symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
        df = pd.DataFrame()
        used_symbol = ""

        with st.spinner(
            f"正在鎖定台股代號 {stock_digits} 抓取歷史數據，依據犀利媽心法計算 RSI 並動態聯網獲取新聞..."
        ):
            try:
                for sym in symbols_to_try:
                    temp_df = yf.download(
                        sym, period="6mo", interval="1d", progress=False
                    )
                    if not temp_df.empty:
                        df = temp_df
                        used_symbol = sym
                        break

                if df.empty:
                    st.error(
                        f"找不到台股代號【{stock_digits}】的數據，請確認代號是否正確（僅支援台股上市櫃股票）。"
                    )
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        close_prices = df[("Close", used_symbol)]
                        high_prices = df[("High", used_symbol)]
                        low_prices = df[("Low", used_symbol)]
                        volume = df[("Volume", used_symbol)]
                    else:
                        close_prices = df["Close"]
                        high_prices = df["High"]
                        low_prices = df["Low"]
                        volume = df["Volume"]

                    df["RSI_5"] = calculate_rsi(close_prices, window=5)
                    df["RSI_10"] = calculate_rsi(close_prices, window=10)

                    latest_close = float(close_prices.iloc[-1])
                    latest_high = float(high_prices.iloc[-1])
                    latest_low = float(low_prices.iloc[-1])
                    latest_diff = latest_high - latest_low
                    latest_rsi_5 = float(df["RSI_5"].iloc[-1])
                    latest_rsi_10 = float(df["RSI_10"].iloc[-1])
                    
                    latest_vol = float(volume.iloc[-1])
                    avg_vol_5 = float(volume.tail(5).mean())
                    is_volume_up = latest_vol > avg_vol_5

                    comp_name = stock_name_dict.get(stock_digits, "台股公司")

                    st.success(
                        comp_name + "【" + used_symbol + "】最新收盤價：" + str(round(latest_close, 2)) + " 元"
                    )

                    col_h, col_l, col_diff, col_c = st.columns(4)
                    with col_h:
                        st.metric(label="🔺 本日最高", value=f"{latest_high:.2f}")
                    with col_l:
                        st.metric(label="🔻 本日最低", value=f"{latest_low:.2f}")
                    with col_diff:
                        st.metric(
                            label="📊 最高最低價差",
                            value=f"{latest_diff:.2f}",
                            delta=f"{(latest_diff / latest_low * 100):.2f}%",
                        )
                    with col_c:
                        st.metric(label="💵 最新收盤", value=f"{latest_close:.2f}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
                    with col2:
                        st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

                    # ==========================================
                    # 🎯 犀利媽 20年極端心法核心判定引擎
                    # ==========================================
                    st.markdown("---")
                    st.subheader("🎯 犀利媽 20年極端心法實戰報告")

                    min_rsi = min(latest_rsi_5, latest_rsi_10)
                    max_rsi = max(latest_rsi_5, latest_rsi_10)

                    if max_rsi >= 80:
                        market_state = "🔥 極端過熱區 (RSI: " + str(round(max_rsi, 1)) + ")：高檔過熱，隨時有急跌拉回風險。"
                    elif min_rsi <= 20:
                        market_state = "❄️ 極端超跌區 (RSI: " + str(round(min_rsi, 1)) + ")：進入非理性恐慌低檔區，隨時注意止跌反彈！"
                    elif min_rsi <= 35:
                        market_state = "📉 偏弱超賣區 (RSI: " + str(round(min_rsi, 1)) + ")：指標逐漸偏弱接近低檔，密切觀察是否破底。"
                    elif max_rsi >= 65:
                        market_state = "📈 偏強過熱區 (RSI: " + str(round(max_rsi, 1)) + ")：指標偏強拉升中，隨時注意高檔追價風險。"
                    else:
                        market_state = "⚖️ 常態雜訊區 (RSI: " + str(round(min_rsi, 1)) + "~" + str(round(max_rsi, 1)) + ")：30~70 盤整中，犀利媽視為無效訊號。"

                    if max_rsi >= 85:
                        light = "🔴 賣出燈 (極端過熱)"
                        score = 15
                        action = "【心法執行】高檔爆量不漲，果斷獲利了結或順勢放空，絕不追高！"
                    elif min_rsi <= 20:
                        if is_volume_up:
                            light = "🟢 買進燈 (極端超跌 + 主力帶量)"
                            score = 90
                            action = "【心法執行】恐慌急殺且出現帶量止跌，符合犀利媽黃金低接點，分批進場！"
                        else:
                            light = "🔵 觀察燈 (極端超跌等待量能)"
                            score = 75
                            action = "【心法執行】指標已達個位數/低檔極端值，隨時盯盤，等帶量紅K一出立刻手刀買進！"
                    elif min_rsi <= 30:
                        light = "🟡 預警燈 (接近超跌位階)"
                        score = 60
                        action = "【心法執行】指標接近超跌區，先列入重點觀察清單，等 RSI 破 20 更好。"
                    elif max_rsi >= 70:
                        light = "🟠 警戒燈 (過熱拉高區)"
