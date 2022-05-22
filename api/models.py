from typing import Optional
from pydantic import BaseModel


class SearchConfig(BaseModel):
    users: int
    keywords: list[str]
    hashtags: list[str]
    exclude: Optional[list[str]] = None
    countries: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class DiscoverConfig(BaseModel):
    keywords: list[str]
    tweets_per_user: int


class EntitiesConfig(BaseModel):
    person: Optional[bool] = False
    norp: Optional[bool] = False
    fac: Optional[bool] = False
    organization: Optional[bool] = False
    location: Optional[bool] = False
    places: Optional[bool] = False
    product: Optional[bool] = False
    event: Optional[bool] = False
    art: Optional[bool] = False
    law: Optional[bool] = False
    language: Optional[bool] = False
    date: Optional[bool] = False
    time: Optional[bool] = False
    percent: Optional[bool] = False
    money: Optional[bool] = False
    quantity: Optional[bool] = False
    ordinal: Optional[bool] = False
    cardinal: Optional[bool] = False


class ExtractConfig(BaseModel):
    links_per_user: int
    entities: Optional[EntitiesConfig] = {}


class Config(BaseModel):
    searching: SearchConfig
    discovery: DiscoverConfig
    extraction: ExtractConfig
