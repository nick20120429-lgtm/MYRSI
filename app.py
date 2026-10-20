import pandas as pd
import streamlit as st
import yfinance as yf

# 網頁標題
st.title("📈 台股專用 RSI 智慧查詢與診斷工具")
st.write(
    "本工具**僅支援台灣股市**。支援直接輸入**中文公司名稱**（例如：台積電、緯創、鴻海）"
    "或**數字代號**（例如：2330、3605），點擊確定後將自動計算 5T 與 10T RSI 並提供買賣策略建議。"
)


# 快取機制：自動從證交所抓取所有台股上市櫃公司的「中文名稱與代號」清單
@st.cache_data(ttl=86400)  # 快取一天，避免每次點擊都重新下載
def get_stock_name_mapping():
  mapping = {}
  try:
    # 1. 抓取上市股票清單 (證交所)
    url_twse = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    df_twse = pd.read_html(url_twse)[0]
    df_twse.columns = df_twse.iloc[0]
    df_twse = df_twse.iloc[1:]

    for _, row in df_twse.iterrows():
      # 欄位通常包含「有價證券代號及名稱」 (例如: "2330 台積電")
      col_val = str(row.iloc[0])
      if " " in col_val:
        parts = col_val.split(" ", 1)
        if len(parts) == 2:
          code, name = parts[0].strip(), parts[1].strip()
          if len(code) == 4 and code.isdigit():
            mapping[name] = code

    # 2. 抓取上櫃股票清單 (櫃買中心)
    url_tpex = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4"
    df_tpex = pd.read_html(url_tpex)[0]
    df_tpex.columns = df_tpex.iloc[0]
    df_tpex = df_tpex.iloc[1:]

    for _, row in df_tpex.iterrows():
      col_val = str(row.iloc[0])
      if " " in col_val:
        parts = col_val.split(" ", 1)
        if len(parts) == 2:
          code, name = parts[0].strip(), parts[1].strip()
          if len(code) == 4 and code.isdigit():
            mapping[name] = code

  except Exception as e:
    # 若聯絡不上官方網站，提供基本備用對照
    mapping = {
        "台積電": "2330",
        "緯創": "3231",
        "鴻海": "2317",
        "聯發科": "2454",
        "廣達": "2382",
    }

  return mapping


# 載入對照表
stock_name_map = get_stock_name_mapping()

# 使用欄位排版讓輸入框跟按鈕並排
col_input, col_btn = st.columns([3, 1])

with col_input:
  stock_input = st.text_input(
      "請輸入台股代號或中文名稱（例如 台積電、2330）：",
      value="台積電",
      label_visibility="collapsed",
  )

with col_btn:
  st.write("")
  submit_btn = st.button("確定查詢", type="primary")

if submit_btn and stock_input:
  raw_input = stock_input.strip()

  # 判斷使用者輸入的是中文名稱還是代號
  if raw_input in stock_name_map:
    stock_digits = stock_name_map[raw_input]
    st.info(f"偵測到您輸入【{raw_input}】，已自動對應至台股代號：{stock_digits}")
  else:
    # 如果不是直接對應到名稱，就過濾出數字
    stock_digits = "".join(filter(str.isdigit, raw_input))

  if not stock_digits:
    st.error(
        "找不到該公司名稱，請確認輸入是否正確（例如：台積電、緯創、或直接輸入代號"
        " 2330）！"
    )
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
            advice = "短線漲幅過快，買氣過熱。若有持股可考慮適度調節，切勿盲目追高。"
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
                "短天期動能大於中天期，且雙雙站在 50 中軸之上，短線買氣回溫，多方佔優勢！"
                "**建議：可考慮進場或加碼。**"
            )
          else:
            status_title = "⚪ **多空拉鋸 / 盤整格局**"
            stars = "⭐⭐⭐"
            symbol_icon = "⚖️"
            advice = "目前數值顯示多空力道均衡，建議觀望，等待方向明確再行操作。"

          st.markdown(f"**目前狀態：** {status_title} {symbol_icon}")
          st.markdown(f"**操作推薦指數：** {stars}")
          st.markdown(f"**買賣策略建議：** {advice}")

          # 顯示近期走勢圖表
          st.markdown("---")
          st.subheader("📊 近期 RSI 走勢圖")
          rsi_chart_df = pd.DataFrame(
              {"RSI_5": df["RSI_5"], "RSI_10": df["RSI_10"]}
          ).tail(30)
          st.line_chart(rsi_chart_df)

      except Exception as e:
        st.error(f"讀取台股資料時發生錯誤：{e}")

# 在頁面下方加入 RSI 核心概念備註說明區塊
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
