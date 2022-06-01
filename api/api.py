import os
import sys
import uuid
import threading
from pprint import pprint

from fastapi import FastAPI, HTTPException
from pyspark import SparkConf, SparkContext

from models import Config, SearchConfig

sys.path.append(f"{os.environ['HOME']}/Thesis_Project/")

from src import test_query_results, pipeline, connect_elasticsearch, PROFILE_FIELDS, NORMAL_LINK_FIELDS, \
    WILDCARD_LINK_FIELDS

conf = SparkConf().setAppName("Thesis").setMaster("local[*]")
spark_context = SparkContext(conf=conf)
app = FastAPI()


@app.post("/search")
async def trigger_pipeline(config: Config):
    search_key = uuid.uuid4()

    t = threading.Thread(target=pipeline, args=(spark_context, config.dict(), search_key))
    t.start()

    return {
        "key": search_key
    }


@app.post("/search/test")
async def test(config: SearchConfig):
    test_tweets = test_query_results({
        "searching": config.dict()
    })

    return {
        "tweets": test_tweets
    }


@app.get("/searches")
async def retrieve_searches(search_after=None):
    _es = connect_elasticsearch()

    res = _es.search(index="searches", body={"query": {"match_all": {}}}, search_after=search_after, size=1000)

    searches = [{'id': search.get('_id'), 'config': search.get('_source')} for search in
                res.get('hits', {}).get('hits', [])]

    return {
        "searches": searches,
        "search_after": res.get("search_after")
    }


@app.get("/searches/{search_id}")
async def retrieve_search(search_id, q=None, fields=None, search_after=None):
    _es = connect_elasticsearch()

    if q is None:
        query = {"match_all": {}}
    else:
        query = {
            "multi_match": {
                "query": q,
                "fields": fields.split(",") if fields is not None else PROFILE_FIELDS,
                "fuzziness": "AUTO"
            }
        }

    try:
        res = _es.search(index=f"search_{search_id}", body={"query": query}, search_after=search_after,
                         size=1000)
    except Exception:
        raise HTTPException(status_code=404, detail="Search not found or did not provide any results.")

    profiles = [profile.get('_source') for profile in res.get('hits', {}).get('hits', [])]

    return {
        "profiles": profiles,
        "search_after": res.get("search_after")
    }


@app.get("/searches/{search_id}/profiles/{profile_id}")
async def retrieve_search(search_id, profile_id, q=None, fields=None, search_after=None):
    _es = connect_elasticsearch()

    if q is None:
        query = {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": profile_id,
                            "default_field": "id"
                        }
                    },
                    {
                        "nested": {
                            "path": "processed_links",
                            "query": {"match_all": {}},
                            "inner_hits": {
                                "size": 100
                            }
                        }
                    }
                ],
            },
        }
    else:
        if fields is not None:
            fields = fields.split(",")

            normal_fields = [field for field in fields if field in NORMAL_LINK_FIELDS]
            wildcard_fields = [field for field in fields if field in WILDCARD_LINK_FIELDS]

            inner_queries = []

            if len(normal_fields) > 0:
                inner_queries.append({"multi_match": {
                    "query": q,
                    "fields": [f"processed_links.{field}" for field in normal_fields],
                    "fuzziness": "AUTO"
                }})

            for field in wildcard_fields:
                inner_queries.append({
                    "wildcard": {
                        f"processed_links.{field}": {"value": f"*{q}*"}
                    }
                })
        else:
            inner_queries = [
                {"multi_match": {
                    "query": q,
                    "fields": [f"processed_links.{field}" for field in NORMAL_LINK_FIELDS],
                    "fuzziness": "AUTO"
                }}
            ]

            for field in WILDCARD_LINK_FIELDS:
                inner_queries.append({
                    "wildcard": {
                        f"processed_links.{field}": {"value": f"*{q}*"}
                    }
                })

        query = {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": profile_id,
                            "default_field": "id"
                        }
                    },
                    {
                        "nested": {
                            "path": "processed_links",
                            "query": {
                                "bool": {
                                    "should": inner_queries
                                }
                            },
                            "inner_hits": {
                                "size": 100
                            }
                        }
                    }
                ],
            },
        }

    try:
        res = _es.search(index=f"search_{search_id}",
                         body={"query": query},
                         search_after=search_after)

        profiles = res.get("hits", {}).get('hits', [])
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Profile not found or did not extract any links.")

    if len(profiles) != 1:
        raise HTTPException(status_code=404, detail="Query did not match any results.")

    links = [link.get("_source") for link in
             profiles[0].get("inner_hits", {}).get("processed_links", {}).get("hits", {}).get("hits", []) if
             link.get("_source") is not None]

    return {
        "links": links,
        "search_after": res.get("search_after")
    }
