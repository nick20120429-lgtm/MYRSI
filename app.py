from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與 RWD 寬螢幕自適應
st.set_page_config(
    page_title="台股 RSI 智慧診斷工具", page_icon="📈", layout="centered"
)

# 注入自訂樣式：輸入框與查詢按鈕高度同為 40px 等高對齊
st.markdown(
    """
    <style>
    /* 輸入框高度設定為 40px */
    .stTextInput input {
        font-size: 16px !important;
        height: 40px !important;
        border-radius: 6px !important;
        border: 1px solid #CBD5E1 !important;
    }
    
    /* 查詢按鈕高度同步設定為 40px，達成等高對齊 */
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
    </style>
    """,
    unsafe_allow_html=True,
)

# 取得台灣當前時間
tz_taiwan = pytz.timezone("Asia/Taipei")
now_taiwan = datetime.now(tz_taiwan)
current_date_str = now_taiwan.strftime("%Y/%m/%d")
current_time_str = now_taiwan.strftime("%H:%M")

# Google 風格精簡 Header 與開發者署名
st.markdown(
    "<div style='text-align: center; margin-bottom: 15px;'>"
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
    "💡 **實戰操作口訣：**\n\n"
    "> * 🚀 **站上 5T（強勢）**：極強勢攻擊 ➔ 短線買進 / 多單續抱\n"
    "> * ⚠️ **跌破 5T（轉弱）**：攻勢受阻、轉弱警訊 ➔ 減碼停利 / 試探性建倉\n"
    "> * 🛑 **跌破 10T（破防）**：趨勢轉空、防線失守 ➔ 全數停損離場 / 加碼放空"
)

st.write(
    "本工具**僅支援台灣股市**。請輸入台股代號（例如：2330、3605 或 2377），"
    "點擊確定後將自動從 Yahoo Finance 抓取台股歷史數據，計算 5T、10T RSI 與極高低價。"
)

# 使用欄位排版讓輸入框跟按鈕並排
col_input, col_btn = st.columns([3, 1])

with col_input:
  stock_input = st.text_input(
      "請輸入台股代號（例如 2330）：", value="2330", label_visibility="collapsed"
  )

with col_btn:
  submit_btn = st.button("確定查詢", type="primary")

if submit_btn and stock_input:
  raw_input = stock_input.strip()
  stock_digits = "".join(filter(str.isdigit, raw_input))

  if not stock_digits:
    st.error("請輸入正確的台股數字代號（例如：2330、3605）！")
  else:
    # 嚴格限定僅抓取台股上市 (.TW) 或上櫃 (.TWO)
    symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
    df = pd.DataFrame()
    used_symbol = ""

    with st.spinner(
        f"正在透過 Yahoo 台灣股市 API 鎖定代號 {stock_digits} 抓取歷史數據..."
    ):
      try:
        for sym in symbols_to_try:
          temp_df = yf.download(sym, period="1y", interval="1d", progress=False)
          if not temp_df.empty and len(temp_df) > 10:
            df = temp_df
            used_symbol = sym
            break

        if df.empty:
          st.error(
              f"找不到台股代號【{stock_digits}】的資料，請確認代號是否正確（僅支援台股上市櫃股票）。"
          )
        else:
          # 確保欄位為單一階層（避免 MultiIndex 造成抓取崩潰）
          if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

          close_prices = df["Close"]
          high_prices = df["High"]
          low_prices = df["Low"]

          # 計算本日、本月、本年最高/最低價
          latest_date = df.index[-1]
          current_year = latest_date.year
          current_month = latest_date.month

          # 本日高低價（最後一個交易日）
          day_high = float(high_prices.iloc[-1])
          day_low = float(low_prices.iloc[-1])

          # 本月高低價
          month_mask = (df.index.year == current_year) & (
              df.index.month == current_month
          )
          month_df = df[month_mask]
          month_high = (
              float(month_df["High"].max()) if not month_df.empty else day_high
          )
          month_low = (
              float(month_df["Low"].min()) if not month_df.empty else day_low
          )

          # 本年高低價
          year_mask = df.index.year == current_year
          year_df = df[year_mask]
          year_high = (
              float(year_df["High"].max()) if not year_df.empty else day_high
          )
          year_low = float(year_df["Low"].min()) if not year_df.empty else day_low


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

          # 顯示 RSI 指標
          col1, col2 = st.columns(2)
          with col1:
            st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
          with col2:
            st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

          # 顯示本日、本月、本年最高最低價區塊
          st.markdown("---")
          st.subheader("📊 價格區間極值統計（本日 / 本月 / 本年）")

          p_col1, p_col2, p_col3 = st.columns(3)
          with p_col1:
            st.metric(
                label="本日最高 / 最低",
                value=f"{day_high:.2f}",
                delta=f"低 {day_low:.2f}",
            )
          with p_col2:
            st.metric(
                label="本月最高 / 最低",
                value=f"{month_high:.2f}",
                delta=f"低 {month_low:.2f}",
            )
          with p_col3:
            st.metric(
                label="本年最高 / 最低",
                value=f"{year_high:.2f}",
                delta=f"低 {year_low:.2f}",
            )

          # 口訣解讀邏輯判定與白話對照輸出
          st.markdown("---")
          st.subheader("🤖 依口訣邏輯進行的系統智慧診斷與操作建議")

          if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
            status_title = "🔴 **極度過熱 / 高檔警戒區**"
            stars = "⭐"
            symbol_icon = "🚨"
            meaning = "短線過熱，買氣來到極高檔，追價意願易竭盡。"
            action = "分批獲利了結、入袋為安！"
          elif latest_rsi_5 > 70:
            status_title = "🟠 **短線過熱（超買區）**"
            stars = "⭐⭐"
            symbol_icon = "🔥"
            meaning = "短線漲幅過快，買氣過熱。"
            action = "適度調節，切勿盲目追高。"
          elif latest_rsi_5 < 50 and latest_rsi_10 < 50:
            status_title = "🔴 **跌破 10T（趨勢轉空）**"
            stars = "⭐⭐"
            symbol_icon = "🛑"
            meaning = (
                "跌破 10T ➔ 代表趨勢轉空、防線失守，過去一段時間的多頭結構遭到破壞。"
            )
            action = "全數停損離場 / 加碼放空"
          elif latest_rsi_5 < 50 and latest_rsi_10 >= 50:
            status_title = "🟡 **跌破 5T（攻勢受阻）**"
            stars = "⭐⭐⭐"
            symbol_icon = "⚠️"
            meaning = (
                "跌破 5T ➔ 代表短線攻勢受阻、出現轉弱警訊（但 10T 中期防線尚存）。"
            )
            action = "減碼停利 / 試探性建立空單"
          elif latest_rsi_5 >= 50 and latest_rsi_10 >= 50:
            status_title = "🟢 **站上 5T（極強勢攻擊）**"
            stars = "⭐⭐⭐⭐⭐"
            symbol_icon = "🚀"
            meaning = "站上 5T ➔ 代表短線動能強勁，為極強勢攻擊盤面！"
            action = "短線買進 / 多單續抱"
          else:
            status_title = "⚪ **多空拉鋸 / 盤整格局**"
            stars = "⭐⭐⭐"
            symbol_icon = "⚖️"
            meaning = "目前數值顯示多空力道均衡，方向尚未明確。"
            action = "建議觀望，等待突破再行操作。"

          st.markdown(f"**目前狀態：** {status_title} {symbol_icon}")
          st.markdown(f"**操作推薦指數：** {stars}")
          st.markdown(f"**📊 股價與均線關係代表意義：** {meaning}")
          st.markdown(f"**🎯 犀利媽的操作動作：** **{action}**")

          # 顯示近期走勢圖表
          st.markdown("---")
          st.subheader("📊 近期 RSI 走勢圖")
          rsi_chart_df = pd.DataFrame(
