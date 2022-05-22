import os
import sys
import uuid
import threading

from fastapi import FastAPI
from pyspark import SparkConf, SparkContext

from models import Config

sys.path.append(f"{os.environ['HOME']}/Thesis_Project/")

from src import test_query_results, pipeline, connect_elasticsearch

conf = SparkConf().setAppName("Thesis").setMaster("local[*]")
spark_context = SparkContext(conf=conf)
app = FastAPI()


@app.get("/test")
async def test():
    test_tweets = test_query_results()

    return {
        "data": test_tweets
    }


@app.post("/search")
async def search(config: Config):
    search_key = uuid.uuid4()

    t = threading.Thread(target=pipeline, args=(spark_context, config.dict(), search_key))
    t.start()

    return {
        "key": search_key
    }


@app.get("/searches")
async def retrieve_searches(search_after=None):
    _es = connect_elasticsearch()

    res = _es.search(index="searches", body={"query": {"match_all": {}}}, search_after=search_after)

    return res


@app.get("/searches/{search_id}")
async def retrieve_search(search_id, search_after=None):
    _es = connect_elasticsearch()

    res = _es.search(index=f"search_{search_id}", body={"query": {"match_all": {}}}, search_after=search_after)

    return res
