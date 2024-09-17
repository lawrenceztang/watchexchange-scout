from whoosh.index import create_in
from whoosh.fields import *
from gpt import *

schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)
ix = create_in("indexdir2", schema)
writer = ix.writer()
writer.add_document(title=u"First document", path=u"/a",
                    content=u"[WTS] Casio G-Shock GW9500-3")
writer.add_document(title=u"Second document", path=u"/b",
                    content=u"The second one is even more interesting!")
writer.commit()
from whoosh.qparser import QueryParser
with ix.searcher() as searcher:
    query = QueryParser("content", ix.schema).parse(get_watch_name("Casio G-Shock GW9500-3"))
    results = searcher.search(query)
    print(results[0])