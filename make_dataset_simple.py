import requests
import re
from lxml import html
from datetime import datetime as dt
import datetime
import time
import csv

def get_reddit(subreddit,listing,limit,timeframe, after=""):
    try:
        base_url = f'https://www.reddit.com/r/{subreddit}/{listing}.json?limit={limit}&t={timeframe}&after={after}'
        request = requests.get(base_url, headers = {'User-agent': 'yourbot'})
    except:
        print('An Error Occured')
        return
    return request.json()

def get_body(comment):
    return comment["data"]["body"]

def get_comments(id):
    url = "https://www.reddit.com/r/watchexchange/comments/%s.json?sort=old" % id
    request = requests.get(url, headers = {'User-agent': 'yourbot'})
    return request.json()[1]["data"]["children"]


filter_list = ["sold", "SOLD"]
def get_in_filter_list(string):
    out = -1
    for filter in filter_list:
        find = string.find(filter)
        if find != -1:
            return find
    return -1

def get_sold(data):
    if data["link_flair_css_class"] == "sold":
        return 1
    return 0

def filter_comment(comment):
    out = -1
    find = get_in_filter_list(comment)

    while find != -1:
        comment = comment[:find] + comment[find + 1:]
        find = get_in_filter_list(comment)
    return comment

sold_count = 0
unsold_count = 0

def get_price(string):
    if not "$" in string:
        return -1
    index = [m.start() for m in re.finditer("\$", string)][-1]
    if index == -1:
        return -1
    try:
        return float(string[index + 1:].split(" ")[0].replace(",", "").replace(".", ""))
    except:
        return -1

def write(string, price, sold):
    global sold_count
    global unsold_count
    if sold == 1:
        sold_count += 1
    else:
        unsold_count += 1
    if sold:
        file = open(base_path + "/" + str(sold) + "/" + str(sold_count), "w+")
    else:
        file = open(base_path + "/" + str(sold) + "/" + str(unsold_count), "w+")
    file.write(string + "\n")
    file.write(str(price))
    file.close()

subreddit = 'watchexchange'
limit = 999999999999
timeframe = 'all' #hour, day, week, month, year, all
listing = 'new' # controversial, best, hot, new, random, rising, top
base_path = "simple_data"


after = ""
count = 0
while True:
    r = get_reddit(subreddit,listing,limit,timeframe, after=after)
    try:
        after = r["data"]["children"][99]["data"]["name"]
    except:
        time.sleep(2)
        continue
    for item in r["data"]["children"]:
        if dt.fromtimestamp(item["data"]["created_utc"]) < dt.now() - datetime.timedelta(days=10):
            title = item["data"]["title"]
            try:
                comment = get_body(get_comments(item["data"]["id"])[1])
            except:
                continue
            comment = filter_comment(comment)
            string = title + comment
            sold = get_sold(item["data"])
            price = get_price(comment)
            if price != -1:
                write(title, price, sold)
    count += 1
    if count % 2 == 0:
        print("%u requests completed" % count)