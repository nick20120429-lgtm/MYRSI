import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與 RWD 寬螢幕自適應
st.set_page_config(
    page_title="台股專用 RSI 智慧查詢與診斷工具", page_icon="📈", layout="centered"
)

# 注入專業級 UI 樣式（美化卡片、適當字體大小、優化手機排版）
st.markdown(
    """
    <style>
    /* 整體主標題與段落微調 */
    h1 {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #1E293B;
    }
    
    /* 輸入框文字與高度優化（適中大小，手機好打不卡字） */
    .stTextInput input {
        font-size: 16px !important;
        height: 45px !important;
        border-radius: 8px !important;
    }
    
    /* 查詢按鈕美化與對齊 */
    .stButton > button {
        height: 45px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        width: 100%;
        border-radius: 8px !important;
        background-color: #2563EB !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #1D4ED8 !important;
    }

    /* 手機版 RWD 微調 */
    @media (max-width: 640px) {
        .stButton > button {
            margin-top: 5px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 網頁標題與開發者署名
st.title("📈 台股 RSI 智慧診斷工具")
st.markdown(
    "<p style='color: #64748B; font-size: 13px; margin-bottom: 0px;'>本工具專為台灣股市設計。請輸入台股代號（例如：2330、3605），系統將自動計算 5T 與 10T RSI 並提供專業操作建議。</p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color: #2563EB; font-size: 12px; font-weight: 600;'>👨‍💻 開發者：尼克范"
    " V.1.020</p>",
    unsafe_allow_html=True,
)

st.markdown("---")

# 搜尋列排版
col_input, col_btn = st.columns([3, 1])

with col_input:
  stock_input = st.text_input(
      "請輸入台股代號", value="2330", label_visibility="collapsed"
  )

with col_btn:
  submit_btn = st.button("查詢")

if submit_btn and stock_input:
  raw_input = stock_input.strip()
  stock_digits = "".join(filter(str.isdigit, raw_input))

  if not stock_digits:
    st.error("請輸入正確的台股數字代號（例如：2330、3605）！")
  else:
    symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
    df = pd.DataFrame()
    used_symbol = ""

    with st.spinner(f"正在擷取代號 {stock_digits} 即時數據並計算 RSI..."):
      try:
        for sym in symbols_to_try:
          temp_df = yf.download(sym, period="6mo", interval="1d", progress=False)
          if not temp_df.empty:
            df = temp_df
            used_symbol = sym
            break

        if df.empty:
          st.error(
              f"找不到代號【{stock_digits}】的資料，請確認代號是否正確（僅支援台股上市櫃股票）。"
          )
        else:
          # 檢查 MultiIndex 欄位結構以正確抓取價格
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

          latest_open = float(open_prices.iloc[-1])
          latest_high = float(high_prices.iloc[-1])
          latest_low = float(low_prices.iloc[-1])
          latest_close = float(close_prices.iloc[-1])
          latest_rsi_5 = float(df["RSI_5"].iloc[-1])
          latest_rsi_10 = float(df["RSI_10"].iloc[-1])

          # 顯示股票代號與當日開盤、收盤等行情資訊
          st.success(f"**【{used_symbol}】 最新交易行情**")

          # 用四欄位整齊呈現：開盤價、最高價、最低價、最新收盤價
          c_p1, c_p2, c_p3, c_p4 = st.columns(4)
          with c_p1:
            st.metric(label="開盤價", value=f"{latest_open:.2f}")
          with c_p2:
            st.metric(label="最高價", value=f"{latest_high:.2f}")
          with c_p3:
            st.metric(label="最低價", value=f"{latest_low:.2f}")
          with c_p4:
            st.metric(label="收盤價", value=f"{latest_close:.2f}")

          # RSI 數據呈現
          col_r1, col_r2 = st.columns(2)
          with col_r1:
            st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
          with col_r2:
            st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

          # 智慧診斷與買賣策略建議區塊
          st.markdown("---")
          st.subheader("🤖 系統智慧診斷與買賣策略")

          # 判定邏輯
          if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
            status_title = "🔴 極度過熱 / 高檔警戒區"
            stars = "⭐"
            symbol_icon = "🚨"
            advice = (
                "5T 或 10T 來到 90 以上極高檔！符合「連續多日高檔、準備賣出」"
                "的訊號特徵。短線過熱，強烈建議分批獲利了結、入袋為安！"
            )
          elif latest_rsi_5 > 70:
            status_title = "🟠 短線過熱（超買區）"
            stars = "⭐⭐"
            symbol_icon = "🔥"
            advice = "短線漲幅過快，買氣過熱。若有持股可考慮適度調節，切勿盲目追高。"
          elif latest_rsi_5 < 30 and latest_rsi_10 < 40:
            status_title = "🔴 短線超賣 / 弱勢"
            stars = "⭐⭐"
            symbol_icon = "🤒"
            advice = (
                "短線跌幅較重進入超賣區。若中期指標（10T）也跟著崩跌，需注意停損；"
                "若 10T 仍有守，可觀察是否有打底機會。"
            )
          elif latest_rsi_5 < latest_rsi_10 and latest_rsi_10 >= 50:
            status_title = "🟡 高檔技術性回檔 / 整理中"
            stars = "⭐⭐⭐"
            symbol_icon = "🛡️"
            advice = (
                "短線買氣稍微降溫（5T < 50），但中期多頭防線（10T >= 50）仍穩固。"
                "**建議：持股續抱，耐心等待短線止穩。**"
            )
          elif latest_rsi_5 > latest_rsi_10 and latest_rsi_5 >= 50:
            status_title = "🟢 短線轉強 / 多頭買入訊號"
            stars = "⭐⭐⭐⭐⭐"
            symbol_icon = "🚀"
            advice = (
                "短天期動能大於中天期，且雙雙站在 50 中軸之上，短線買氣回溫，多方佔優勢！"
                "**建議：可考慮進場或加碼。**"
            )
          else:
            status_title = "⚪ 多空拉鋸 / 盤整格局"
            stars = "⭐⭐⭐"
            symbol_icon = "⚖️"
            advice = "目前數值顯示多空力道均衡，建議觀望，等待方向明確再行操作。"

          st.markdown(f"**目前狀態：** {status_title} {symbol_icon}")
          st.markdown(f"**操作推薦指數：** {stars}")
          st.info(f"**買賣策略建議：**\n\n{advice}")

          # 走勢圖表
          st.markdown("---")
          st.subheader("📊 近期 RSI 走勢圖")
          rsi_chart_df = pd.DataFrame(
              {"RSI_5": df["RSI_5"], "RSI_10": df["RSI_10"]}
          ).tail(30)
          st.line_chart(rsi_chart_df)

      except Exception as e:
        st.error(f"讀取台股資料時發生錯誤：{e}")

# 底部可折疊的 RSI 觀念備註
st.markdown("---")
with st.expander("📖 點擊展開：RSI 的核心概念與數值範圍說明"):
  st.markdown("""
    * **數值範圍**：介於 0 到 100 之間。
    * **多空分水嶺（50）**：
        * **RSI > 50**：代表買方力道較強（多方市場）。
        * **RSI < 50**：代表賣方力道較強（空方市場）。
    * **超買與超賣區間**：
        * **RSI ≥ 70 或 80（甚至 90+）**：進入超買區（市場過熱，短線有回檔或下跌風險，高檔連續多日可準備賣出）。
        * **RSI ≤ 30 或 20**：進入超賣區（市場過冷，短線有反彈或上漲機會）。
    """)
