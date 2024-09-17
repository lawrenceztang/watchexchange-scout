import requests
from lxml import html
# from notify_run import Notify
from datetime import datetime as dt
import datetime
import time
from make_search_index import get_sold_listings
from gpt import *


def get_reddit(subreddit, listing, limit, timeframe):
    try:
        base_url = f'https://www.reddit.com/r/{subreddit}/{listing}.json?limit={limit}&t={timeframe}'
        request = requests.get(base_url, headers={'User-agent': 'yourbot'})
    except:
        print('An Error Occured')
    return request.json()


def get_comments(id):
    url = "https://www.reddit.com/r/watchexchange/comments/%s.json?" % id
    request = requests.get(url, headers={'User-agent': 'yourbot'})
    return request.json()[1]["data"]["children"]


def get_body(comment):
    return comment["data"]["body"]


def chrono_listings(watch_name):
    url = f"https://www.chrono24.com/search/index.htm?query={watch_name}&dosearch=true&sortorder=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    r = requests.get(url, headers=headers)

    try:
        tree = html.fromstring(r.content)
        list = tree.xpath(
            "//div[contains(@class, 'd-flex') and contains(@class, 'justify-content-between') and contains(@class, 'align-items-end') and contains(@class, 'm-b-1')]/div/div[@class='text-bold']/text()")
        list = [str(e) for e in list if e[0] != "\n"]
    except:
        return []

    if not list:
        return []

    # i = 0
    # while i < len(list):
    #     try:
    #         list[i] = int(list[i].replace(",", ""))
    #     except:
    #         try:
    #             del list[i]
    #         except:
    #             break
    #         i -= 1
    #     i += 1

    return list


def get_watch_price(comments):
    for item in comments[1:]:
        body = get_body(item)
        price = get_price(body)
        if price != -1:
            return price, body
    return None, "Not found"


def should_flip_chrono(title, listing_body, chrono_listings):
    query = f"""
    You are given a listing on a Reddit watch exchange forum. You are also given prices of the watch on Chrono24. Determine if you can buy the watch off of Reddit and flip it for a profit.

    Listing:
    {title}
    {listing_body}

    Chrono24 Prices:
    {chrono_listings}
    """
    messages = [{"role": "user", "content": query}]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    query2 = "Now respond to the question with Yes or No."
    messages = [{"role": "user", "content": query},
                {"role": "assistant", "content": response.choices[0].message.content},
                {"role": "user", "content": query2}]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    return True if response.choices[0].message.content[:2] == "Ye" else False


def should_flip(price, condition, sold_listings):
    if len(sold_listings) < 3:
        return False
    for listing in sold_listings:
        if listing[1] < price:
            return False
    return True


# notify = Notify()
client = OpenAI()

subreddit = 'watchexchange'
limit = 99999
timeframe = 'week'  # hour, day, week, month, year, all
listing = 'new'  # controversial, best, hot, new, random, rising, top
seen = set()

while True:
    r = get_reddit(subreddit, listing, limit, timeframe)
    for item in r["data"]["children"]:
        if item["data"]["id"] in seen:
            break
        if dt.fromtimestamp(item["data"]["created_utc"]) > dt.now() - datetime.timedelta(minutes=1000):
            title = item["data"]["title"]
            thumbnail = item["data"]["thumbnail"]
            comments = get_comments(item["data"]["id"])
            price, listing_body = get_watch_price(comments)
            if price != None:
                watch_name = get_watch_name(title)
                condition = get_condition(listing_body)
                sold_listings = get_sold_listings(watch_name, condition)
                print("Watch name: %s" % watch_name)
                print("Price: %f" % price)
                print("Condition: %s" % condition)
                print(sold_listings)
                if price != -1 and should_flip(price, condition, sold_listings):
                    print("You should flip this watch")
                    # notify.send(watch_name + ": " + str(price))
                print("\n\n")
    time.sleep(10 * 60)