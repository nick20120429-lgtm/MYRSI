import os
import urllib.parse
import pandas as pd
import streamlit as st
import yfinance as yf
import feedparser

# 頁面寬度設定與標題
st.set_page_config(page_title="犀利媽極端 RSI 與動態新聞分析工具", page_icon="📈", layout="wide")

# 頂部開發者資訊與圖片展示區塊
col_img, col_header = st.columns([1, 4])

with col_img:
    image_path = "avatar.png"
    if os.path.exists(image_path):
        st.image(image_path, width=110)

with col_header:
    st.markdown("**開發者：尼克范 2026.10.20.V6 最終整合版**")
    st.title("📈 犀利媽 20年極端心法與即時新聞動態分析工具")

st.write("本工具**支援全台灣上市櫃股票**。請輸入台股代號（例如：2330、6239、3231、2317）：")
st.write(
    "💡 **犀利媽 20年核心哲學**：「常態區間不看雜訊、極端行情絕不手軟、對照消息面靈活操作、破支撐手刀停損！」"
)

# 常用台股中文名稱對照字典（若未在字典中，程式會自動以代號搜尋新聞）
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
}

def fetch_stock_news(stock_code, stock_name, count=10):
    """
    透過 Google/Yahoo 財經新聞 RSS 動態抓取該台股最新的即時新聞與重大消息（至少 10 則）
    """
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

col_input, col_btn = st.columns([3, 1])

with col_input:
    stock_input = st.text_input(
        "請輸入台股代號（例如 6239）：", value="6239", label_visibility="collapsed"
    )

with col_btn:
    st.write("")
    submit_btn = st.button("確定查詢", type="primary")

if submit_btn and stock_input:
    raw_input = stock_input.strip()
    stock_digits = "".join(filter(str.isdigit, raw_input))

    if not stock_digits:
        st.error("請輸入正確的台股數字代號（例如：2330、6239）！")
    else:
        symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
        df = pd.DataFrame()
        used_symbol = ""

        with st.spinner(
            f"正在鎖定台股代號 {stock_digits} 抓取歷史數據、計算極端 RSI 並聯網獲取最新 10+ 則新聞..."
        ):
            try:
                for sym in symbols_to_try:
                    temp_df = yf.download(
                        sym, period="6mo", interval="1d", progress=False
                    )
                    if not temp_df.empty:
                        df = temp_df
                        used_symbol = sym
                        break

                if df.empty:
                    st.error(
                        f"找不到台股代號【{stock_digits}】的數據，請確認代號是否正確（僅支援台股上市櫃股票）。"
                    )
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        close_prices = df[("Close", used_symbol)]
                        high_prices = df[("High", used_symbol)]
                        low_prices = df[("Low", used_symbol)]
                        volume = df[("Volume", used_symbol)]
                    else:
                        close_prices = df["Close"]
                        high_prices = df["High"]
                        low_prices = df["Low"]
                        volume = df["Volume"]

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
                    latest_high = float(high_prices.iloc[-1])
                    latest_low = float(low_prices.iloc[-1])
                    latest_diff = latest_high - latest_low
                    latest_rsi_5 = float(df["RSI_5"].iloc[-1])
                    latest_rsi_10 = float(df["RSI_10"].iloc[-1])
                    
                    latest_vol = float(volume.iloc[-1])
                    avg_vol_5 = float(volume.tail(5).mean())
                    is_volume_up = latest_vol > avg_vol_5

                    comp_name = stock_name_dict.get(stock_digits, "台股公司")

                    st.success(
                        f"{comp_name}【{used_symbol}】最新收盤價：{latest_close:.2f} 元"
                    )

                    col_h, col_l, col_diff, col_c = st.columns(4)
                    with col_h:
                        st.metric(label="🔺 本日最高", value=f"{latest_high:.2f}")
                    with col_l:
                        st.metric(label="🔻 本日最低", value=f"{latest_low:.2f}")
                    with col_diff:
                        st.metric(
                            label="📊 最高最低價差",
                            value=f"{latest_diff:.2f}",
                            delta=f"{(latest_diff / latest_low * 100):.2f}%",
                        )
                    with col_c:
                        st.metric(label="💵 最新收盤", value=f"{latest_close:.2f}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
                    with col2:
                        st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

                    # ==========================
                    # 🎯 犀利媽 20年極端心法判定核心
                    # ==========================
                    st.markdown("---")
                    st.subheader("🎯 犀利媽 20年極端心法實戰報告")

                    if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
                        light = "🔴 賣出燈 (極端過熱警戒)"
                        score = 15
                        conclusion = "市場極度過熱（高檔鈍化或隨時回檔）"
                        action = "【心法執行】果斷獲利了結或順勢放空，絕不追高！"
                    elif latest_rsi_5 <= 10 or latest_rsi_10 <= 15:
                        if is_volume_up:
                            light = "🟢 買進燈 (極端超跌 + 帶量)"
                            score = 90
                            conclusion = "非理性恐慌急殺，且有主力帶量護盤"
                            action = "【心法執行】分批進場低接搶反彈，嚴設停損。"
                        else:
                            light = "🔵 觀察燈 (極端超跌但量能不足)"
                            score = 65
                            conclusion = "進入極端超跌區，但量能偏冷"
                            action = "【心法執行】持續盯盤，等待帶量紅K出現再出手。"
                    else:
                        light = "⚪ 觀望燈 (常態雜訊區)"
                        score = 50
                        conclusion = "常態震盪區（無極端訊號）"
                        action = "【心法執行】按兵不動，專注盯緊少數核心主流股，絕不亂槍打鳥。"

                    if latest_rsi_5 >= 80 or latest_rsi_10 >= 80:
                        market_state = "🔥 **極端過熱區**：RSI 飆高，隨時有急跌反轉風險。"
                    elif latest_rsi_5 <= 20 or latest_rsi_10 <= 20:
                        market_state = "❄️ **極端超跌區**：RSI 進入個位數或低檔，留意恐慌盤後的反彈契機。"
                    else:
                        market_state = "⚖️ **常態雜訊區**：RSI 停留在 30~70 之間（犀利媽視為無效盤整區，完全不管）。"

                    st.markdown("#### 📋 犀利媽 20 年極端心法檢視報告：")
                    st.markdown(f"1. **【心法 1】極端值過濾**：{market_state}")
                    st.markdown(f"2. **【心法 2】持股精品化**：專注主流焦點股。當前量能狀態：{'🔥 具備人氣與成交量' if is_volume_up else '❄️ 成交量偏冷，建議觀望'}")
                    st.markdown(f"3. **【心法 3】消息與籌碼對照**：請對照下方即時新聞與重大消息，技術指標需配合基本面題材驗證！")
                    st.markdown(
                        f"4. **【心法 4】鐵血停損紀律**：\n"
                        f"   - **燈號判定**：{light}（評分：{score}/100）\n"
                        f"   - **操作方針**：{action}\n"
                        f"   - **⚠️ 鐵血原則**：方向不對或破支撐立刻**手刀停損**，絕不抱持「套牢變存股」的鴕鳥心態！"
                    )

                    # ===== 一眼看懂面板 =====
                    st.markdown("---")
                    col_a, col_b, col_c_status = st.columns(3)
                    with col_a:
                        st.metric("燈號", light)
                    with col_b:
                        st.metric("評分", f"{score}/100")
                    with col_c_status:
                        st.metric("建議方針", action.split("】")[1] if "】" in action else action)

                    st.progress(score)

                    # 顯示近期走勢圖表
                    st.markdown("---")
                    st.subheader("📊 近期 RSI 走勢圖")
                    rsi_chart_df = pd.DataFrame(
                        {"RSI_5": df["RSI_5"], "RSI_10": df["RSI_10"]}
                    ).tail(60)
                    st.line_chart(rsi_chart_df)

                    # =======================================================
                    # 📰 放在最下方：動態抓取該股最新 10 則新聞與重大消息
                    # =======================================================
                    st.markdown("---")
                    st.subheader(f"📰【{comp_name} ({stock_digits})】最新即時新聞與重大消息（動態抓取 10 則）")
                    
                    fetched_news = fetch_stock_news(stock_digits, comp_name, count=10)

                    if fetched_news:
                        for idx, item in enumerate(fetched_news, 1):
                            st.markdown(
                                f"**{idx}. [{item['title']}]({item['link']})**  \n"
                                f"⏱️ *發布時間：{item['date']}* | 🏢 *來源：{item['source']}*"
                            )
                            st.markdown("---")
                    else:
                        st.info("尚無查獲近期相關新聞，請至公開資訊觀測站參閱該股公告。")

            except Exception as e:
                st.error(f"讀取台股資料時發生錯誤：{e}")

# 頁面最下方心法備註說明
st.markdown("---")
with st.expander("📖 點擊展開：犀利媽 20 年極端操盤四大鐵則"):
    st.markdown("""
    1. **只抓極端值**：平時常態區間（30~70）的指標雜訊完全無視；唯有極端過熱（>90）或極端超跌（<10）才動作。
    2. **開精品店不開雜貨店**：持股精簡至 2~3 檔主流焦點股，不碰無量冷門股與低價水餃股。
    3. **消息與極端指標雙軌驗證**：主動解讀財經資訊，反向利用群體恐慌或過度樂觀。
    4. **絕不凹單、手刀停損**：方向不對立刻砍單，確保資金流動性與冷靜的思考能力。
    """)
