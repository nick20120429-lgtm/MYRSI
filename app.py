# ===========================
# 犀利媽法則分析
# ===========================

st.markdown("---")
st.subheader("🎯 犀利媽法則分析")

if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:

    status = "🔴 極度過熱區"
    stars = "⭐"
    score = 20

    advice = """
• RSI 已進入極度過熱區
• 不建議追價
• 建議分批獲利了結
"""

elif latest_rsi_5 >= 70:

    status = "🟠 過熱警戒區"
    stars = "⭐⭐"
    score = 40

    advice = """
• 短線漲幅過大
• 不建議新資金追高
• 持股可續抱觀察
"""

elif latest_rsi_5 > latest_rsi_10 and latest_rsi_5 >= 50:

    status = "🟢 多頭攻擊區"
    stars = "⭐⭐⭐⭐⭐"
    score = 95

    advice = """
• 5T 大於 10T
• 短線動能強於中期
• 多方主導盤勢
• 可考慮買進或加碼
"""

elif latest_rsi_5 < latest_rsi_10 and latest_rsi_10 >= 50:

    status = "🟡 多頭整理區"
    stars = "⭐⭐⭐⭐"
    score = 80

    advice = """
• 中期趨勢仍維持多頭
• 短線技術性整理
• 建議續抱等待
"""

elif latest_rsi_5 < 30 and latest_rsi_10 < 40:

    status = "🔵 超賣觀察區"
    stars = "⭐⭐⭐"
    score = 75

    advice = """
• 已進入超賣區
• 留意是否出現反彈
• 可觀察布局機會
"""

else:

    status = "⚪ 觀望區"
    stars = "⭐⭐⭐"
    score = 50

    advice = """
• 多空拉鋸
• 方向尚未明確
• 建議觀望
"""

# ===== 一眼看懂 =====

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.metric(
        "目前狀態",
        status
    )

with col_b:
    st.metric(
        "推薦指數",
        stars
    )

with col_c:
    st.metric(
        "買進評分",
        f"{score}/100"
    )

st.progress(score)

# ===== 犀利媽結論 =====

if score >= 90:

    st.success(f"""
【犀利媽結論】

{status}

買進評分：{score}/100

✅ 可買進

✅ 可加碼

✅ 持股續抱
""")

elif score >= 75:

    st.info(f"""
【犀利媽結論】

{status}

買進評分：{score}/100

✅ 持股續抱

✅ 等待下一次攻
