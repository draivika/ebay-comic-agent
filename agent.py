import requests
import datetime
import random
import hashlib
import os
from xml.sax.saxutils import escape

# Placeholder config import
from config import EBAY_APP_ID

CATEGORY_ID = "63"  # eBay category for Comics
MAX_ENTRIES = 50

def get_last_week_dates():
    today = datetime.datetime.utcnow()
    last_week = today - datetime.timedelta(days=7)
    return last_week.strftime("%Y-%m-%dT00:00:00.000Z"), today.strftime("%Y-%m-%dT00:00:00.000Z")

def fetch_sold_listings():
    start_time, end_time = get_last_week_dates()
    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    params = {
        "OPERATION-NAME": "findCompletedItems",
        "SERVICE-VERSION": "1.13.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "categoryId": CATEGORY_ID,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "sortOrder": "EndTimeSoonest",
        "paginationInput.entriesPerPage": MAX_ENTRIES,
        "outputSelector": "PictureURLSuperSize"
    }
    response = requests.get(url, params=params)
    return response.json()

def analyze_results(data):
    try:
        items = data['findCompletedItemsResponse'][0]['searchResult'][0]['item']
    except (KeyError, IndexError):
        return None, "No data returned."

    prices = []
    for item in items:
        try:
            prices.append(float(item['sellingStatus'][0]['currentPrice'][0]['__value__']))
        except:
            continue

    if not prices:
        return None, "No valid prices."

    avg_price = sum(prices) / len(prices)
    top_item = max(items, key=lambda x: float(x['sellingStatus'][0]['currentPrice'][0]['__value__']))

    title = top_item['title'][0]
    link = top_item['viewItemURL'][0]
    thumb = top_item.get('galleryURL', [""])[0]
    price = float(top_item['sellingStatus'][0]['currentPrice'][0]['__value__'])

    headline = f"Comic Book Market Watch: Avg Price ${avg_price:.2f}, Top Sale ${price:.2f}"
    summary = (
        f"This week’s eBay Comics market saw {len(prices)} notable sales with an average price of ${avg_price:.2f}. "
        f"The top sale was \"{title}\" for ${price:.2f}. Stay tuned weekly for pricing trends and key shifts."
    )
    return {
        "headline": headline,
        "summary": summary,
        "title": title,
        "link": link,
        "thumbnail": thumb,
        "price": price
    }, None

def write_html(report):
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(f"""
<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='UTF-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1.0'>
  <meta name="robots" content="noindex">
  <title>{report['headline']}</title>
</head>
<body>
  <h1>{report['headline']}</h1>
  <p>{report['summary']}</p>
  <h2>Top Sale</h2>
  <a href="{report['link']}" target="_blank">
    <img src="{report['thumbnail']}" alt="{report['title']}" style="max-width:300px;">
    <p>{report['title']} – ${report['price']:.2f}</p>
  </a>
</body>
</html>
        """)

def write_rss(report):
    now = datetime.datetime.utcnow()
    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S +0000")
    item = f"""
<item>
  <title>{escape(report['headline'])}</title>
  <link>https://yourusername.github.io/ebay-comic-agent/report.html</link>
  <description>{escape(report['summary'])}</description>
  <pubDate>{pub_date}</pubDate>
</item>
    """
    rss = f"""
<?xml version="1.0"?>
<rss version="2.0">
<channel>
  <title>eBay Comic Market Pulse</title>
  <link>https://yourusername.github.io/ebay-comic-agent/</link>
  <description>Weekly summary of eBay sold comic listings</description>
  {item}
</channel>
</rss>
    """
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss.strip())

def main():
    data = fetch_sold_listings()
    report, err = analyze_results(data)
    if err:
        print("Error:", err)
        return
    write_html(report)
    write_rss(report)
    print("Report and RSS feed updated.")

if __name__ == "__main__":
    main()
