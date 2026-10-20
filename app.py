from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與 RWD 寬螢幕自適應
st.set_page_config(
    page_title="犀利媽台股 RSI 智慧診斷工具", page_icon="📈", layout="centered"
)

# 注入專業級 UI 樣式（排版整齊劃一、間距與區塊優化）
st.markdown(
    """
    <style>
    /* 整體區塊最大寬度與上下留白控制 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 720px;
    }
    
    /* 標題統一樣式 */
    h1 {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #0F172A;
        margin-bottom: 0px !important;
    }
    
    /* 輸入框高度與圓角一致化 */
    .stTextInput input {
        font-size: 16px !important;
        height: 42px !important;
        border-radius: 6px !important;
        border: 1px solid #CBD5E1 !important;
    }
    
    /* 按鈕高度與對齊一致化 */
    .stButton > button {
        height: 42px !important;
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

    /* 指標面板 (st.metric) 外觀整齊劃一 */
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

    /* 資訊提示框與分隔線間距微調 */
    div.stInfo {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 4px solid #2563EB !important;
        border-radius: 6px !important;
    }
    hr {
        margin: 1rem 0px !important;
        border-color: #E2E8F0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 網頁標題
st.title("📈 台股專用 RSI 智慧查詢與診斷工具")
st.write(
    "本工具**僅支援台灣股市**。請輸入台股代號（例如：2330、3605 或 5347），"
    "點擊確定後將自動計算 5T 與 10T RSI 並對照買賣策略提供燈號建議。"
)

# 使用欄位排版讓輸入框跟按鈕並排
col_input, col_btn = st.columns([3, 1])

with col_input:
  stock_input = st.text_input(
      "請輸入台股代號（例如 2330）：", value="2330", label_visibility="collapsed"
  )

with col_btn:
  st.write("")
  submit_btn = st.button("確定查詢", type="primary")

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

          # 結合圖片邏輯與多空判定的智慧診斷
          st.markdown("---")
          st.subheader("🤖 系統智慧診斷與買賣策略建議")

          # 判定邏輯
          if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
            status_title = "🔴 **極度過熱 / 高檔警戒區**"
            stars = "⭐"
            symbol_icon = "🚨"
            advice = (
                "5T 或 10T 來到 90 以上極高檔！符合「連續多日高檔、準備賣出」"
                "的訊號特徵。短線過熱，強烈建議分批獲利了結、入袋為安！"
            )
          elif latest_rsi_5 > 70:
            status_title = "🟠 **短線過熱（超買區）**"
            stars = "⭐⭐"
            symbol_icon = "🔥"
            advice = (
                "短線漲幅過快，買氣過熱。若有持股可考慮適度調節，切勿盲目追高。"
            )
          elif latest_rsi_5 < 30 and latest_rsi_10 < 40:
            status_title = "🔴 **短線超賣 / 弱勢**"
            stars = "⭐⭐"
            symbol_icon = "🤒"
            advice = (
                "短線跌幅較重進入超賣區。若中期指標（10T）也跟著崩跌，需注意停損；"
                "若 10T 仍有守，可觀察是否有打底機會。"
            )
          elif latest_rsi_5 < latest_rsi_10 and latest_rsi_10 >= 50:
            status_title = "🟡 **高檔技術性回檔 / 整理中**"
            stars = "⭐⭐⭐"
            symbol_icon = "🛡️"
            advice = (
                "短線買氣稍微降溫（5T < 50），但中期多頭防線（10T >= 50）仍穩固。"
                "**建議：持股續抱，耐心等待短線止穩。**"
            )
          elif latest_rsi_5 > latest_rsi_10 and latest_rsi_5 >= 50:
            status_title = "🟢 **短線轉強 / 多頭買入訊號**"
            stars = "⭐⭐⭐⭐⭐"
            symbol_icon = "🚀"
            advice = (
                "短天期動能大於中天期，且雙雙站在 50"
                " 中軸之上，短線買氣回溫，多方佔優勢！"
                "**建議：可考慮進場或加碼。**"
            )
          else:
            status_title = "⚪ **多空拉鋸 / 盤整格局**"
            stars = "⭐⭐⭐"
            symbol_icon = "⚖️"
            advice = (
                "目前數值顯示多空力道均衡，建議觀望，等待方向明確再行操作。"
            )

          st.markdown(f"**目前狀態：** {status_title} {symbol_icon}")
          st.markdown(f"**操作推薦指數：** {stars}")
          st.markdown(f"**買賣策略建議：** {advice}")

          # 顯示近期走勢圖表
          st.markdown("---")
          st.subheader("📊 近期 RSI 走勢圖")
          rsi_chart_df = pd.DataFrame(
              {"RSI_5": df["RSI_5"], "RSI_10": df["RSI_10"]}
          ).tail(30)
          st.line_chart(rsi_chart_df, height=220)

      except Exception as e:
        st.error(f"讀取台股資料時發生錯誤：{e}")

# 在頁面下方加入 RSI 核心概念備註說明區塊
st.markdown("---")
with st.expander("📖 點擊展開：RSI 的核心概念與數值範圍說明"):
  st.markdown(
      """
    * **數值範圍**：介於 0 到 100 之間。
    * **多空分水嶺（50）**：
        * **RSI > 50**：代表買方力道較
