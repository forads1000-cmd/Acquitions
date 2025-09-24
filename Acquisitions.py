import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import pandas as pd
import io
 
# Keyword buckets
KEYWORDS = {
    "M&A": [
        "acquisition", "acquires", "acquires stake", "buys", 
        "merger", "merges with", "takeover", "deal"
    ],
    "Expansion": [
        "new factory", "new plant", "greenfield project", "brownfield project",
        "facility expansion", "new unit", "setting up plant", "capacity expansion",
        "manufacturing hub"
    ],
    "Partnerships": [
        "joint venture", "JV", "strategic partnership", "collaboration"
    ]
}
 
# Search terms (Google News RSS)
SEARCH_TERMS = [
    "company acquisition",
    "corporate acquisition",
    "startup acquisition",
    "merger and acquisition",
    "business acquisition",
    "new factory",
    "new plant",
    "capacity expansion",
    "joint venture"
]
 
# Only last 1 day
cutoff_date = datetime.now() - timedelta(days=1)
 
def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()
 
def classify_article(title):
    title_lower = title.lower()
    for category, words in KEYWORDS.items():
        for w in words:
            if w in title_lower:
                return category
    return None
 
def fetch_articles(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "xml")
    items = soup.find_all("item")
    results = []
    for item in items:
        title = item.title.text
        link = item.link.text
        pub_date = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
        if pub_date < cutoff_date:
            continue
 
        category = classify_article(title)
        if not category:
            continue
 
        results.append({
            "date": pub_date.strftime("%Y-%m-%d"),
            "title": clean_text(title),
            "link": link,
            "category": category
        })
    return results
 
def main():
    st.title("📢 Daily Corporate Activity Signals")
    st.write("Flagging **M&A / Expansion / Fundraising / Partnerships** from news articles in the last 24h.")
 
    all_results = []
    for term in SEARCH_TERMS:
        all_results.extend(fetch_articles(term))
 
    unique_results = {r["title"]: r for r in all_results}.values()
    df = pd.DataFrame(unique_results)
 
    if not df.empty:
        st.success(f"Found {len(df)} relevant news articles")
        st.dataframe(df)
 
        # Export to Excel with hyperlinks
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Signals", index=False)
            workbook  = writer.book
            worksheet = writer.sheets["Signals"]
 
            # Title col
            title_col = df.columns.get_loc("title")
            link_col = df.columns.get_loc("link")
 
            for row in range(len(df)):
                url = df.iloc[row, link_col]
                text = df.iloc[row, title_col]
                worksheet.write_url(row + 1, title_col, url, string=text)
 
        st.download_button(
            label="📥 Download Excel",
            data=output.getvalue(),
            file_name=f"daily_signals_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No relevant signals found today.")
 
if __name__ == "__main__":
    main()
