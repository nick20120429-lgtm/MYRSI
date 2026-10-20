from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與 RWD 寬螢幕自適應
st.set_page_config(
    page_title="犀利媽台股 RSI 智慧診斷工具", page_icon="📈", layout="centered"
)

# 注入專業級 UI 樣式（緊湊排版、減少空白、優化手機與桌機視覺）
st.markdown(
    """
    <style>
    /* 縮減上方留白，讓版面更緊湊專業 */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* 標題與段落間距微調 */
    h1 {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #1E293B;
        margin-bottom: 0px !important;
    }
    
    /* 下拉選單與按鈕高度優化 */
    .stSelectbox div[data-baseweb="select"] {
        min-height: 40px !important;
    }
    
    /* 查詢按鈕美化與對齊 */
    .stButton > button {
        height: 40px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        width: 100%;
        border-radius: 6px !important;
        background-color: #2563EB !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #1D4ED8 !important;
    }

    /* 縮小 st.metric 的上下空白與邊距，使其更緊湊 */
    div[data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 8px 12px;
        border-radius: 8px;
    }
    div[data-testid="stMetric"] label {
        font-size: 13px !important;
        color: #64748B !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 20px !important;
        font-weight: 700 !important;
    }

    /* 減少分隔線的垂直空間 */
    hr {
        margin: 0.8em 0px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 取得台灣當前時間
tz_taiwan = pytz.timezone("Asia/Taipei")
now_taiwan = datetime.now(tz_taiwan)
current_date_str = now_taiwan.strftime("%Y/%m/%d")
current_time_str = now_taiwan.strftime("%H:%M")

# 網頁標題與開發者署名
st.title("📈 犀利媽台股 RSI 智慧診斷工具")
st.markdown(
    f"<p style='color: #64748B; font-size: 12px; margin-bottom: 2px;'>📅"
    f" <b>日期：</b>{current_date_str} 🕒"
    f" <b>時間：</b>{current_time_str} | <span style='color: #2563EB;"
    " font-weight: 600;'>👨‍💻 尼克范 V.1.020</span></p>",
    unsafe_allow_html=True,
)

# 🚀 犀利媽主頁固定口訣醒目看板
st.info(
    "💡 **犀利媽實戰口訣：**\n\n> *「5T 過熱先入袋，10T 守住多頭在；超跌見紅不急追，低接耐心等待來。」*"
)

st.markdown("---")

# 純自選股快速切換清單（可在此直接增減你想看的股票）
favorite_stocks = {
    "3605 宏致": "3605",
    "2377 微星": "2377",
    "2330 台積電": "2330",
    "2317 鴻海": "2317",
    "2603 長榮": "2603",
    "2454 聯發科": "2454",
}

col_sel, col_btn = st.columns([3, 1])

with col_sel:
  selected_fav = st.selectbox(
      "選擇關注的股票", list(favorite_stocks.keys()), label_visibility="collapsed"
  )

with col_btn:
  submit_btn = st.button("查詢")

# 只要切換下拉選單或點擊查詢按鈕，就直接載入數據
stock_digits = favorite_stocks[selected_fav]

if submit_btn or selected_fav:
  symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
  df = pd.DataFrame()
  used_symbol = ""

  with st.spinner("正在載入行情與計算 RSI..."):
    try:
      for sym in symbols_to_try:
        temp_df = yf.download(sym, period="5d", interval="1d", progress=False)
        if not temp_df.empty:
          df = temp_df
          used_symbol = sym
          break

      if df.empty:
        st.error(
            f"找不到代號【{stock_digits}】的資料，請確認代號是否正確（僅支援台股上市櫃股票）。"
        )
      else:
        if isinstance(df.columns, pd.MultiIndex):
          close_prices = df[("Close", used_symbol)]
          open_prices = df[("Open", used_symbol)]
          high_prices = df[("High", used_symbol)]
          low_prices = df[("Low", used_symbol)]
        else:
          close_prices = df["Close"]
          open_prices = df["Open"]
          high_prices = df["High"]
          low_prices = df["Low"]

        df_long = yf.download(sym, period="6mo", interval="1d", progress=False)
        if isinstance(df_long.columns, pd.MultiIndex):
          long_close = df_long[("Close", used_symbol)]
        else:
          long_close = df_long["Close"]


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
          rs = avg_gain / avg_loss
          rsi = 100 - (100 / (1 + rs))
          return rsi


        rsi_5_series = calculate_rsi(long_close, window=5)
        rsi_10_series = calculate_rsi(long_close, window=10)

        latest_open = float(open_prices.iloc[-1])
        latest_high = float(high_prices.iloc[-1])
        latest_low = float(low_prices.iloc[-1])
        latest_close = float(close_prices.iloc[-1])
        latest_rsi_5 = float(rsi_5_series.iloc[-1])
        latest_rsi_10 = float(rsi_10_series.iloc[-1])

        price_diff = latest_high - latest_low
        price_diff_pct = (
            (price_diff / latest_low) * 100 if latest_low > 0 else 0
        )
        last_date_str = str(df.index[-1].strftime("%Y-%m-%d"))

        market_closed = (
            now_taiwan.hour > 13
            or (now_taiwan.hour == 13 and now_taiwan.minute >= 30)
        )

        st.markdown(
            f"**【{used_symbol}】 即時行情與報價** <span style='color:"
            f" #64748B; font-size: 12px;'>({last_date_str})</span>",
            unsafe_allow_html=True,
        )

        if market_closed:
          c_p1, c_p2, c_p3, c_p4 = st.columns(4)
          with c_p1:
            st.metric(label="本日開盤", value=f"{latest_open:.2f}")
          with c_p2:
            st.metric(label="最高價", value=f"{latest_high:.2f}")
          with c_p3:
            st.metric(label="最低價", value=f"{latest_low:.2f}")
          with c_p4:
            st.metric(label="收盤價", value=f"{latest_close:.2f}")
        else:
          c_p1, c_p2, c_p3, c_p4 = st.columns(4)
          with c_p1:
            st.metric(label="本日開盤", value=f"{latest_open:.2f}")
          with c_p2:
            st.metric(label="盤中最高", value=f"{latest_high:.2f}")
          with c_p3:
            st.metric(label="盤中最低", value=f"{latest_low:.2f}")
          with c_p4:
            st.metric(
                label="即時價格", value=f"{latest_close:.2f}", delta="交易中"
            )

        c_d1, c_d2 = st.columns(2)
        with c_d1:
          st.metric(label="↕️ 本日高低差 (高-低)", value=f"{price_diff:.2f} 元")
        with c_d2:
          st.metric(label="📊 本日振幅比例", value=f"{price_diff_pct:.2f}%")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
          st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
        with col_r2:
          st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

        st.markdown("---")
        st.markdown("**🤖 犀利媽實戰診斷與操作建議**", unsafe_allow_html=True)

        history_tip = ""
        if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
          status_title = "🔴 極度過熱 / 高檔警戒區"
          stars = "⭐"
          advice = (
              "5T 或 10T 來到 90 以上極高檔！符合「連續多日高檔、準備賣出」"
              "的訊號特徵。短線過熱，強烈建議分批獲利了結、入袋為安！"
          )
          history_tip = (
              "💡 **犀利媽經驗談：** 歷史統計顯示，短線衝高至 90"
              " 以上時，追價意願易竭盡，通常 1-3 天內容易出現明顯回檔整理。"
          )
        elif latest_rsi_5 > 70:
          status_title = "🟠 短線過熱（超買區）"
          stars = "⭐⭐"
          advice = (
              "短線漲幅過快，買氣過熱。若有持股可考慮適度調節，切勿盲目追高。"
          )
          history_tip = (
              "💡 **犀利媽經驗談：** 5T
