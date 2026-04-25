import streamlit as st
import requests
import xmltodict

# # RSS sources
# sources = {
#     "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
#     "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
#     "Dainik Bhaskar": "https://www.bhaskar.com/rss-v1--category-1061.xml",
#     "ABP Majha": "https://marathi.abplive.com/rss/featured-articles.xml",
#     "Dainik Jagran": "https://www.jagran.com/rss/news/national.xml",
#     "Aaj Tak": "https://www.aajtak.in/rss",
#     "India Today": "https://www.indiatoday.in/rss/home"
# }

# # Category feeds
# categories = {
#     "General": [{"name": "Times of India", "url": sources["Times of India"]}],
#     "Sports": [{"name": "TOI Sports", "url": "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms"}],
#     "Politics": [{"name": "The Hindu Politics", "url": sources["The Hindu"]}],
#     "Technology": [{"name": "India Today Tech", "url": "https://www.indiatoday.in/technology/rss"}],
#     "Market": [{"name": "Economic Times Market", "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"}]
# }

# # App UI
# st.set_page_config(page_title="📰 Personalized News Aggregator", layout="wide")

# st.title("📰 Personalized News Aggregator")
# st.markdown("### Select News Sources & Category")

# selected_sources = st.multiselect("Choose your news sources", options=list(sources.keys()))
# selected_category = st.selectbox("Choose a category", options=["-- None --"] + list(categories.keys()))

# # Ask the news bot
# st.markdown("### 🤖 Ask the News Bot")
# bot_query = st.text_input("Ask anything e.g., tech news, politics, etc.")

# News fetching function


def fetch_news(feed_urls):
    news_items = []
    for feed in feed_urls:
        try:
            response = requests.get(feed["url"])
            data = xmltodict.parse(response.content)
            items = data["rss"]["channel"]["item"]
            for item in items:
                news_items.append({
                    "title": item.get("title", "No Title"),
                    "link": item.get("link", "#"),
                    "source": feed["name"]
                })
        except Exception as e:
            st.warning(f"Error fetching from {feed['name']}: {e}")
    return news_items

# # Display News Button
# if st.button("Get News") or bot_query:
#     feeds_to_fetch = []

#     # Add selected sources
#     for src in selected_sources:
#         feeds_to_fetch.append({"name": src, "url": sources[src]})

#     # Add selected category
#     if selected_category != "-- None --":
#         feeds_to_fetch.extend(categories[selected_category])

#     # Add bot logic - simple keyword-based redirection
#     if bot_query:
#         for cat in categories:
#             if cat.lower() in bot_query.lower():
#                 feeds_to_fetch.extend(categories[cat])
#                 st.markdown(f"🔍 Showing results for **{cat}** based on your question.")

#     # Fetch & display news
#     news = fetch_news(feeds_to_fetch)

#     if news:
#         st.subheader("🗞️ News Results:")
#         for item in news:
#             st.markdown(f"- [{item['title']}]({item['link']}) _(Source: {item['source']})_")
#     else:
#         st.info("No news found for the selected options.")
