from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與 RWD 寬螢幕自適應
st.set_page_config(
    page_title="犀利媽台股 RSI 智慧診斷工具", page_icon="📈", layout="centered"
)

# 注入專業級 UI 樣式（精緻外框、柔和背景、專業金融儀表板風格）
st.markdown(
    """
    <style>
    /* 整體版面留白與背景微調 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 750px;
    }
    
    /* 標題專業化 */
    h1 {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 0px !important;
    }
    
    /* 輸入框美化 */
    .stTextInput input {
        font-size: 16px !important;
        height: 44px !important;
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
    }
    .stTextInput input:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
    }
    
    /* 查詢按鈕專業化 */
    .stButton > button {
        height: 44px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        width: 100%;
        border-radius: 8px !important;
        background-color: #2563EB !important;
        color: white !important;
        border: none !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }

    /* 金融卡片式指標面板 (st.metric) */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 12px 16px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    div[data-testid="stMetric"] label {
        font-size: 13px !important;
        color: #64748B !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }

    /* 口訣與建議區塊風格優化 */
    div.stInfo {
        background-color: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        border-left: 5px solid #2563EB !important;
        border-radius: 8px !important;
        color: #1E293B !important;
    }

    /* 分隔線 */
    hr {
        margin: 1.2rem 0px !important;
        border-color: #E2E8F0 !important;
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
    f"<p style='color: #64748B; font-size: 12px; margin-top: 4px;"
    f" margin-bottom: 16px;'>📅 <b>日期：</b>{current_date_str} 🕒"
    f" <b>時間：</b>{current_time_str} | <span style='color: #2563EB;"
    " font-weight: 600;'>👨‍💻 尼克范 V.1.020</span></p>",
    unsafe_allow_html=True,
)

# 🚀 犀利媽主頁固定口訣醒目看板
st.info(
    "💡 **犀利媽實戰口訣：**\n\n> *「5T 過熱先入袋，10T 守住多頭在；超跌見紅不急追，低接耐心等待來。」*"
)

st.markdown("")

# 使用欄位排版讓輸入框跟按鈕並排
col_input, col_btn = st.columns([3, 1])

with col_input:
  stock_input = st.text_input(
      "請輸入台股代號：",
      value="",
      placeholder="請輸入代號 (例如: 2330)",
      label_visibility="collapsed",
  )

with col_btn:
  submit_btn = st.button("確定查詢", type="primary")

if submit_btn and stock_input:
  raw_input = stock_input.strip()
  stock_digits = "".join(filter(str.isdigit, raw_input))

  if not stock_digits:
    st.error("⚠️ 請輸入正確的台股數字代號（例如：2330、3605）！")
  else:
    symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
    df = pd.DataFrame()
    used_symbol = ""

    with st.spinner(
        f"🔍 正在鎖定台股代號 {stock_digits} 抓取歷史數據並精準計算 RSI..."
    ):
      try:
        for sym in symbols_to_try:
          temp_df = yf.download(sym, period="6mo", interval="1d", progress=False)
          if not temp_df.empty:
            df = temp_df
            used_symbol = sym
            break

        if df.empty:
          st.error(
              f"❌ 找不到台股代號【{stock_digits}】的資料，請確認代號是否正確（僅支援台股上市櫃股票）。"
          )
        else:
          if isinstance(df.columns, pd.MultiIndex):
            close_prices = df[("Close", used_symbol)]
          else:
            close_prices = df["Close"]


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


          df["RSI_5"] = calculate_rsi(close_prices, window=5)
          df["RSI_10"] = calculate_rsi(close_prices, window=10)

          latest_close = float(close_prices.iloc[-1])
          latest_rsi_5 = float(df["RSI_5"].iloc[-1])
          latest_rsi_10 = float(df["RSI_10"].iloc[-1])
          last_date_str = str(df.index[-1].strftime("%Y-%m-%d"))

          st.markdown("---")
          st.markdown(
              f"📌 **【{used_symbol}】 最新收盤價：**"
              f" <span style='font-size: 18px; color: #2563EB; font-weight:"
              f" 700;'>{latest_close:.2f} 元</span>"
              f" <span style='color: #64748B; font-size:"
              f" 12px;'>({last_date_str})</span>",
              unsafe_allow_html=True,
          )
          st.markdown("")

          col1, col2 = st.columns(2)
          with col1:
            st.metric(label="📊 5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
          with col2:
            st.metric(label="📊 10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

          # 智慧診斷與買賣策略
          st.markdown("---")
          st.markdown(
              "### 🤖 系統智慧診斷與買賣策略建議", unsafe_allow_html=True
          )

          history_tip = ""
          if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
            status_title = "🔴 **極度過熱 / 高檔警戒區**"
            stars = "⭐"
            symbol_icon = "🚨"
            advice = (
                "5T 或 10T 來到 90 以上極高檔！符合「連續多日高檔、準備賣出」"
                "的訊號特徵。短線過熱，強烈建議分批獲利了結、入袋為安！"
            )
            history_tip = (
                "💡 **犀利媽經驗談：** 歷史統計顯示，短線衝高至 90"
                " 以上時，追價意願易竭盡，通常 1-3 天內容易出現明顯回檔整理。"
            )
          elif latest_rsi_5 > 70:
            status_title = "🟠 **短線過熱（超買區）**"
            stars = "⭐⭐"
            symbol_icon = "🔥"
            advice = (
