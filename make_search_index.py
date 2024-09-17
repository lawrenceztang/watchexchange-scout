import json
import whoosh.index as index
from whoosh.fields import *
from tqdm import tqdm
import openai
from openai import OpenAI
import os
from datetime import datetime as dt
import bsddb3 as bsddb
import pickle
from whoosh.qparser import QueryParser
from gpt import *


db_path = 'mydata.db'
chunk_size = 10000

def load_ndjson(filepath, chunk_size=10000):
    with open(filepath, 'r') as f:
        chunk = []
        for i, line in enumerate(f):
            chunk.append(json.loads(line))
            if (i + 1) % chunk_size == 0:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

def create_submissions():
    submissions = load_ndjson("reddit/Watchexchange_submissions")
    total_submissions = sum(1 for _ in open("reddit/Watchexchange_submissions", 'r'))
    schema = Schema(title=TEXT(stored=True), id=TEXT(stored=True), link=TEXT(stored=True))
    ix = index.create_in("indexdir", schema)
    writer = ix.writer()
    with tqdm(total=total_submissions // chunk_size, desc="Processing Submissions") as pbar:
        for chunk in submissions:
            for submission in chunk:
                if submission["link_flair_text"] == "Sold" and dt.fromtimestamp(
                        int(submission["created_utc"])) > dt.now() - datetime.timedelta(days=730):
                    writer.add_document(title=submission["title"], id=submission["id"], link="reddit.com" + submission["permalink"])
            pbar.update(1)
    writer.commit()

def create_comments():
    comments = load_ndjson("reddit/Watchexchange_comments")
    total_comments = sum(1 for _ in open("reddit/Watchexchange_comments", 'r'))
    db = bsddb.hashopen(db_path, 'c')
    with tqdm(total=total_comments // chunk_size, desc="Processing Comments") as pbar:
        for chunk in comments:
            for comment in chunk:
                try:
                    parent_id = comment["parent_id"][3:].encode('utf-8')
                    if parent_id not in db:
                        db[parent_id] = pickle.dumps([])  # Initialize an empty list in bytes

                        # Retrieve the list, append the comment, and store it back
                    temp_list = pickle.loads(db[parent_id])  # Deserialize the list
                    if len(temp_list) < 2:
                        temp_list.append(comment["body"])  # Modify the list
                        db[parent_id] = pickle.dumps(temp_list)  # Serialize and store back
                except:
                    pass
            pbar.update(1)
    db.close()

def get_sold_listings(query, condition="All"):

    if not index.exists_in("indexdir"):
        create_submissions()
    if not os.path.exists(db_path):
        create_comments()

    ix = index.open_dir("indexdir")
    db = bsddb.hashopen(db_path, 'c')

    out = []
    with ix.searcher() as searcher:
        parsed_query = QueryParser("title", ix.schema).parse(query)
        results = searcher.search(parsed_query, limit=20)
        print(f"{len(results)} results retrieved")
        for result in results:
            if len(out) >= 5:
                break
            temp = [result['title']]
            key = result['id'].encode('utf-8')
            if key in db:
                comments_list = pickle.loads(db[key])
                if len(comments_list) >= 2:
                    result_condition = get_condition(comments_list[1])
                    if condition == "All" or result_condition == condition:
                        price = get_price(comments_list[1])
                        if price == -1:
                            continue
                        temp.append(price)
                        temp.append(result_condition)
                        temp.append(result["link"])
                        out.append(temp)
    return out

if __name__ == "__main__":
    out = get_sold_listings("Christopher Ward C60 Trident Pro", condition="All")
    print(out)