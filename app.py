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
    st.markdown("**開發者：尼克范 2026.10.21.V13（語法完全修復終極版）**")
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

def fetch_stock_news(stock_code, stock_name, count=10):
    search_query = f"{stock_code} {stock_name}" if stock_name != "台股公司" else stock_code
    encoded_query = urllib.parse.quote(search_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}+when:30d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    if feed.entries:
        for entry in feed.entries[:count]:
            pub_date = getattr(entry, "published", "")[:16] if hasattr(entry, "published") else ""
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

                    def calculate_rsi(data, window=14):
                        delta = data.diff()
                        gain = delta.clip(lower=0)
                        loss = -delta.clip(upper=0)
                        avg_gain = gain.ewm(
                            alpha=1 / window, min_periods=window, adjust=False
                        ).mean()
                        avg_loss = loss.ewm(
                            alpha=1 / window, min_periods=window, adjust=False
                        ).mean()
                        rs
