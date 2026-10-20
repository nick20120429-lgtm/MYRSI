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
    .block-container {
        padding-top: 1.2rem !important;
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

# 使用欄位排版讓輸入框跟按鈕並排（預設保持空白）
col_input, col_btn = st.columns([3, 1])

with col_input:
  stock_input = st.text_input(
      "請輸入台股代號（例如 2330、3605）：",
      value="",
      placeholder="請輸入台股代號...",
      label_visibility="collapsed",
  )

with col_btn:
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
                "短線漲幅過快，買氣過熱。若有持股可考慮適度調節，切勿盲目追高。"
            )
            history_tip = (
                "💡 **犀利媽經驗談：** 5T 進入 70"
                " 以上超買區時切忌急躁追高，多看少做或分批減碼為宜。"
            )
          elif latest_rsi_5 < 30 and latest_rsi_10 < 40:
            status_title = "🔴 **短線超賣 / 弱勢**"
            stars = "⭐⭐"
            symbol_icon = "🤒"
            advice = (
                "短線跌幅較重進入超賣區。若中期指標（10T）也跟著崩跌，需注意停損；"
                "若 10T 仍有守，可觀察是否有打底機會。"
            )
            history_tip = (
                "💡 **犀利媽經驗談：** 當 5T 跌破 30"
                " 時往往伴隨恐慌殺盤，此時不宜盲目殺低，應觀察 10T"
                " 是否能發揮防守支撐。"
            )
          elif latest_rsi_5 < latest_rsi_10 and latest_rsi_10 >= 50:
            status_title = "🟡 **高檔技術性回檔 / 整理中**"
            stars = "⭐⭐⭐"
            symbol_icon = "🛡️"
            advice = (
                "短線買氣稍微降溫（5T < 50），但中期多頭防線（10T >= 50）仍穩固。"
                "**建議：持股續抱，耐心等待短線止穩。**"
            )
            history_tip = (
                "💡 **犀利媽經驗談：** 10T 保持在 50"
                " 以上代表中多格局未破，短線拉回屬於技術性洗盤，不用過度恐慌。"
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
            history_tip = (
                "💡 **犀利媽經驗談：** 雙指標站在 50"
                " 之上且短天期向上翻揚，為標準的多頭攻擊盤，可順勢關注。"
            )
          else:
            status_title = "⚪ **多空拉鋸 / 盤整格局**"
            stars = "⭐⭐⭐"
            symbol_icon = "⚖️"
            advice = (
                "目前數值顯示多空力道均衡，建議觀望，等待方向明確再行操作。"
            )
            history_tip = (
                "💡 **犀利媽經驗談：** 盤整盤多看少做，等待突破訊號再出手勝率更高。"
            )

          st.markdown(f"**目前狀態：** {status_title} {symbol_icon}")
          st.markdown(f"**操作推薦指數：** {stars}")
          st.info(f"**買賣策略建議：**\n\n{advice}\n\n{history_tip}")

          # 顯示近期走勢圖表
          st.markdown("---")
          st.subheader("📊 近期 RSI 走勢圖")
          rsi_chart_df = pd.DataFrame(
              {"RSI_5": df["RSI_5"], "RSI_10": df["RSI_10"]}
          ).tail(30)
          st.line_chart(rsi_chart_df, height=200)

      except Exception as e:
        st.error(f"讀取台股資料時發生錯誤：{e}")

# 在頁面下方加入 RSI 核心概念備註說明區塊
st.markdown("---")
with st.expander("📖 點擊展開：RSI 的核心概念與數值範圍說明"):
  st.markdown(
      """
    * **數值範圍**：介於 0 到 100 之間。
    * **多空分水嶺（50）**：
        * **RSI > 50**：代表買方力道較強（多方市場）。
        * **RSI < 50**：代表賣方力道較強（空方市場）。
    * **超買與超賣區間**：
        * **RSI ≥ 70 或 80（甚至 90+）**：進入超買區（市場過熱，短線有回檔或下跌風險，高檔連續多日可準備賣出）。
        * **RSI ≤ 30 或 20**：進入超賣區（市場過冷，短線有反彈或上漲機會）。
    """
  )
