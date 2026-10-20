from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與 RWD 寬螢幕自適應
st.set_page_config(
    page_title="台股專用 RSI 智慧查詢與診斷工具", page_icon="📈", layout="centered"
)

# 注入專業級 UI 樣式（緊湊排版、減少空白、優化手機與桌機視覺）
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    h1 {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #1E293B;
        margin-bottom: 0px !important;
    }
    .stTextInput input {
        font-size: 16px !important;
        height: 40px !important;
        border-radius: 6px !important;
    }
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
    hr {
        margin: 1em 0px !important;
    }
    @media (max-width: 640px) {
        .stButton > button {
            margin-top: 0px;
        }
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
st.title("📈 台股 RSI 智慧診斷工具")
st.markdown(
    f"<p style='color: #64748B; font-size: 12px; margin-bottom: 2px;'>📅"
    f" <b>日期：</b>{current_date_str} 🕒"
    f" <b>時間：</b>{current_time_str} | <span style='color: #2563EB;"
    " font-weight: 600;'>👨‍💻 尼克范 V.1.020</span></p>",
    unsafe_allow_html=True,
)

st.markdown("---")

# 搜尋列排版
col_input, col_btn = st.columns([3, 1])

with col_input:
  stock_input = st.text_input(
      "請輸入台股代號", value="3605", label_visibility="collapsed"
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

    with st.spinner("資料與即時行情載入中..."):
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
          # 檢查 MultiIndex 欄位結構
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

          # 計算精準的 5T 與 10T RSI
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

          # 行情數值方塊
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
                  label="即時價格",
                  value=f"{latest_close:.2f}",
                  delta="交易中",
              )

          c_d1, c_d2 = st.columns(2)
          with c_d1:
            st.metric(
                label="↕️ 本日高低差 (高-低)", value=f"{price_diff:.2f} 元"
            )
          with c_d2:
            st.metric(
                label="📊 本日振幅比例", value=f"{price_diff_pct:.2f}%"
            )

          # --- 🚀 外掛嵌入：直接帶出玩股網即時走勢與五檔畫面 ---
          st.markdown("---")
          st.markdown(
              f"**🌐 玩股網即時走勢與五檔 ({stock_digits})**",
              unsafe_allow_html=True,
          )

          wantgoo_url = f"https://www.wantgoo.com/stock/{stock_digits}"
          st.components.v1.iframe(wantgoo_url, height=450, scrolling=True)
          # ----------------------------------------------------

          # RSI 數據呈現
          col_r1, col_r2 = st.columns(2)
          with col_r1:
            st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
          with col_r2:
            st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

          # 智慧診斷與買賣策略建議區塊
          st.markdown("---")
          st.markdown(
              "**🤖 系統智慧診斷與買賣策略**", unsafe_allow_html=True
          )

          if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
            status_title = "🔴 極度過熱 / 高檔警戒區"
            stars = "⭐"
            advice = (
                "5T 或 10T 來到 90 以上極高檔！符合「連續多日高檔、準備賣出」"
                "的訊號特徵。短線過熱，強烈建議分批獲利了結、入袋為安！"
            )
          elif latest_rsi_5 > 70:
            status_title = "🟠 短線過熱（超買區）"
            stars = "⭐⭐"
            advice = (
                "短線漲幅過快，買氣過熱。若有持股可考慮適度調節，切勿盲目追高。"
            )
          elif latest_rsi_5 < 30 and latest_rsi_10 < 40:
            status_title = "🔴 短線超賣 / 弱勢"
            stars = "⭐⭐"
            advice = (
                "短線跌幅較重進入超賣區。若中期指標（10T）也跟著崩跌，需注意停損；"
                "若 10T 仍有守，可觀察是否有打底機會。"
            )
          elif latest_rsi_5 < latest_rsi_10 and latest_rsi_10 >= 50:
            status_title = "🟡 高檔技術性回檔 / 整理中"
            stars = "⭐⭐⭐"
            advice = (
                "短線買氣稍微降溫（5T < 50），但中期多頭防線（10T >= 50）仍穩固。"
                "**建議：持股續抱，耐心等待短線止穩。**"
            )
          elif latest_rsi_5 > latest_rsi_10 and latest_rsi_5 >= 50:
            status_title = "🟢 短神轉強 / 多頭買入訊號"
            stars = "⭐⭐⭐⭐⭐"
            advice = (
                "短天期動能大於中天期，且雙雙站在 50 中軸之上，短線買氣回溫，多方佔優勢！"
                "**建議：可考慮進場或加碼。**"
            )
          else:
            status_title = "⚪ 多空拉鋸 / 盤整格局"
            stars = "⭐⭐⭐"
            advice = (
                "目前數值顯示多空力道均衡，建議觀望，等待方向明確再行操作。"
            )

          st.markdown(f"**目前狀態：** {status_title}")
          st.markdown(f"**操作推薦指數：** {stars}")
          st.info(f"**買賣策略建議：**\n\n{advice}")

          # RSI 走勢圖
          st.markdown("---")
          st.markdown("**📊 近期 RSI 走勢圖**", unsafe_allow_html=True)
          rsi_chart_df = pd.DataFrame(
              {"RSI_5": rsi_5_series, "RSI_10": rsi_10_series}
          ).tail(30)
          st.line_chart(rsi_chart_df, height=200)

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
