from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與 RWD 寬螢幕自適應
st.set_page_config(
    page_title="台股 RSI 智慧診斷工具", page_icon="📈", layout="centered"
)

# 注入 Google 風格的極簡專業 UI 樣式
st.markdown(
    """
    <style>
    /* 整體區塊置中與寬度控制，營造 Google 搜尋首頁感 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 650px;
    }
    
    /* 隱藏預設標題邊距 */
    h1 {
        display: none;
    }
    
    /* 輸入框高度與圓角（Google 搜尋框風格） */
    .stTextInput input {
        font-size: 16px !important;
        height: 48px !important;
        border-radius: 24px !important;
        border: 1px solid #dfe1e5 !important;
        padding-left: 20px !important;
        box-shadow: 0 1px 6px rgba(32,33,36,0.05);
    }
    .stTextInput input:focus {
        border-color: rgba(223,225,229,0) !important;
        box-shadow: 0 1px 6px rgba(32,33,36,0.28) !important;
    }
    
    /* 查詢按鈕風格（Google 搜尋按鈕感） */
    .stButton > button {
        height: 42px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        width: 100%;
        border-radius: 20px !important;
        background-color: #f8f9fa !important;
        color: #3c4043 !important;
        border: 1px solid #f8f9fa !important;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        background-color: #f1f3f4 !important;
        border: 1px solid #dadce0 !important;
        color: #202124 !important;
    }

    /* 指標面板 (st.metric) 外觀 */
    div[data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 10px 14px;
        border-radius: 8px;
    }
    div[data-testid="stMetric"] label {
        font-size: 13px !important;
        color: #64748B !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 20px !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }

    /* 資訊提示框與分隔線 */
    div.stInfo {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 4px solid #4285F4 !important;
        border-radius: 8px !important;
    }
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

# --- Google 風格精簡 Header ---
st.markdown(
    "<div style='text-align: center; margin-bottom: 20px;'>"
    "<h2 style='font-weight: 700; color: #202124; margin-bottom: 5px;'>📈"
    " 台股 RSI 智慧診斷工具</h2>"
    f"<p style='color: #70757a; font-size: 12px;'>📅 <b>日期：</b>{current_date_str}"
    f" 🕒 <b>時間：</b>{current_time_str} | <span style='color: #4285F4;"
    " font-weight: 600;'>👨‍💻 尼克范 V.1.0.2.0</span></p>"
    "</div>",
    unsafe_allow_html=True,
)

# 固定實戰口訣看板
st.info(
    "💡 **實戰口訣：**\n\n> *「5T 過熱先入袋，10T 守住多頭在；超跌見紅不急追，低接耐心等待來。」*"
)

st.markdown("")

# Google 風格置中簡潔輸入與查詢區
col_spacer1, col_input, col_btn, col_spacer2 = st.columns([0.5, 3, 1.2, 0.5])

with col_spacer1:
  st.empty()

with col_input:
  stock_input = st.text_input(
      "台股代號",
      value="2330",
      placeholder="輸入代號 (例如 2330)",
      label_visibility="collapsed",
  )

with col_btn:
  submit_btn = st.button("台股搜尋", type="primary")

with col_spacer2:
  st.empty()

st.markdown("")

if submit_btn and stock_input:
  raw_input = stock_input.strip()
  stock_digits = "".join(filter(str.isdigit, raw_input))

  if not stock_digits:
    st.error("請輸入正確的台股數字代號（例如：2330、3605）！")
  else:
    symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
    df = pd.DataFrame()
    used_symbol = ""

    with st.spinner(
        f"正在鎖定台股代號 {stock_digits} 抓取歷史數據並精準計算 RSI..."
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
              f"找不到台股代號【{stock_digits}】的資料，請確認代號是否正確（僅支援台股上市櫃股票）。"
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

          st.success(
              f"成功取得台股【{used_symbol}】最新收盤價：{latest_close:.2f} 元"
          )

          col1, col2 = st.columns(2)
          with col1:
            st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
          with col2:
            st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

          # 系統智慧診斷與買賣策略建議
          st.markdown("---")
          st.subheader("🤖 系統智慧診斷與買賣策略建議")

          # 判定邏輯
          if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
            status_title = "🔴 **極度過熱 / 高檔警戒區**"
            stars = "⭐"
            symbol_icon = "🚨"
            advice = (
                "5T 或 10T 來到 90 以上極高檔！符合「連續多日高檔、準備賣出
