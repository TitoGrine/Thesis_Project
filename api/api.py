import os
import sys
import asyncio
from fastapi import FastAPI, Request

sys.path.append(f"{os.environ['HOME']}/Thesis_Project/")

from src.searching import test_query_results

app = FastAPI()


@app.get("/test")
async def test():
    test_tweets = test_query_results()

    return {
        "data": test_tweets
    }
