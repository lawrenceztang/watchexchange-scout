import requests
from lxml import html
# from notify_run import Notify
from datetime import datetime as dt
import datetime
import time
from make_search_index import get_sold_listings, load_ndjson
from gpt import *
import whoosh.index as index
from run_agent import should_flip_algo
from whoosh.fields import *
from tqdm import tqdm
import bsddb3 as bsddb
import pickle

def create_submissions_backtest():
    chunk_size = 10000
    submissions = load_ndjson("reddit/Watchexchange_submissions")
    total_submissions = sum(1 for _ in open("reddit/Watchexchange_submissions", 'r'))
    schema = Schema(title=TEXT(stored=True), id=TEXT(stored=True), link=TEXT(stored=True), sold=TEXT(stored=True))
    ix = index.create_in("indexdir_backtest", schema)
    writer = ix.writer()
    with tqdm(total=total_submissions // chunk_size, desc="Processing Submissions") as pbar:
        for chunk in submissions:
            for submission in chunk:
                if dt.fromtimestamp(int(submission["created_utc"])) > dt.now() - datetime.timedelta(days=730):
                    writer.add_document(title=submission["title"], id=submission["id"], link="reddit.com" + submission["permalink"], sold=submission["link_flair_text"])
            pbar.update(1)
    writer.commit()


# notify = Notify()
client = OpenAI()

subreddit = 'watchexchange'
limit = 99999
timeframe = 'week'  # hour, day, week, month, year, all
listing = 'new'  # controversial, best, hot, new, random, rising, top

# create_submissions_backtest()

db_path = 'mydata.db'
total_should_flip = 0
total_should_flip_and_sold = 0
total_sold = 0
db = bsddb.hashopen(db_path, 'c')

ix = index.open_dir("indexdir_backtest")
all_docs = ix.searcher().documents()
file = open("flip_watches_backtest.txt", "w")
counter = 0
for item in all_docs:
    if counter > 1000:
        break
    key = item['id'].encode('utf-8')
    if key in db:
        comments_list = pickle.loads(db[key])
        comments_list = [{"data": {"body": comment}} for comment in comments_list]
        if "sold" in item and item["sold"] == "Sold":
            total_sold += 1
        if should_flip_algo(item["title"], comments_list, item["link"], file):
            total_should_flip += 1
            if item["sold"] == "Sold":
                total_should_flip_and_sold += 1
            file.write(f"Total should flip that sold: {total_should_flip_and_sold} out of total should flip: {total_should_flip} and total sold: {total_sold} out of: {counter} posts\n\n")
            file.flush()
            print(f"Total should flip that sold: {total_should_flip_and_sold} out of total should flip: {total_should_flip} and total sold: {total_sold} out of: {counter} posts")
        print("\n")
    counter += 1

print(f"Total should flip that sold: {total_should_flip_and_sold} out of total should flip: {total_should_flip} and total sold: {total_sold}")