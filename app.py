import os
import urllib.parse
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
import feedparser
from bs4 import BeautifulSoup
from google import genai

st.set_page_config(page_title="犀利媽 20年極端心法分析工具", page_icon="📈", layout="wide")

# 頂部開發者資訊與圖片展示區塊
col_img, col_header = st.columns([1, 4])

with col_img:
    image_path = "avatar.png"
    if os.path.exists(image_path):
        st.image(image_path, width=110)

with col_header:
    st.markdown("**開發者：尼克范 2026.10.29.V20（財報防護與基本面整合版）**")
    st.title("📈 犀利媽 20年極端心法與財報/MOPS動態分析工具")

st.write("本工具**支援全台灣上市櫃股票**。請輸入台股代號（例如：2330、6239、3231、2317、5347）：")
st.write(
    "💡 **犀利媽 20年核心哲學**：「常態區間不看雜訊、極端行情絕不手軟、財報異常直接剔除、破支撐手刀停損！」"
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
    "3312": "弘憶股",
    "6147": "頎邦",
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

def fetch_financials(ticker_obj):
    """
    透過 yfinance 抓取最近四季的財務報表摘要（營收、淨利、EPS）
    """
    fin_summary = {"status": "無財報資料", "eps_list": [], "revenue_list": []}
    try:
        # 取得損益表
        financials = ticker_obj.financials
        if not financials.empty:
            # 尋找淨利或總營收欄位
            for col in financials.columns[:4]: # 最近四季/年度
                col_date = str(col).split(" ")[0]
                fin_summary["revenue_list"].append(col_date)
        
        # 取得基本財務資訊 (Info)
        info = ticker_obj.info
        fin_summary["pe_ratio"] = info.get("trailingPE", "N/A")
        fin_summary["pb_ratio"] = info.get("priceToBook", "N/A")
        fin_summary["market_cap"] = info.get("marketCap", 0)
        fin_summary["status"] = "財報讀取成功"
    except Exception as e:
        fin_summary["status"] = f"財報解析異常: {str(e)}"
    
    return fin_summary

def fetch_stock_news(stock_code, stock_name, count=5):
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

def fetch_mops_announcements(stock_code, count=5):
    url = "https://mops.twse.com.tw/mops/web/ajax_t05st01"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    payload = {
        "encodeMappingURL": "1",
        "step": "1",
        "firstin": "1",
        "off": "1",
        "queryName": "co_id",
        "incorp": "",
        "typek": "all",
        "co_id": stock_code
    }
    announcements = []
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=6)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        table = soup.find('table', {'class': 'hasBorder'})
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows[:count]:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    date_str = cols[1].text.strip()
                    time_str = cols[2].text.strip()
                    subject = cols[4].text.strip()
                    if subject:
                        announcements.append({
                            "date": f"{date_str} {
