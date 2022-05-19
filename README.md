# Thesis_Project

### Input

To configure the inputs, a file with the name `config.json` should be in the projects directory and have the following
structure.

```json
{
  "searching": {
    "users": "(int) <number of users to try to collect from the tweet search>",
    "keywords": "(array<string>) [<words to search for in tweets>]",
    "hashtags": "(array<string>) [<hashtags to search for in tweets>]",
    "_exclude_": "(array<string>) [<words that can not appear in tweets>]",
    "_countries_": "(array<string>) [<ISO codes of countries to accept tweets from>]",
    "_languages_": "(array<string>) [<BCP 47 identifiers of languages accepted for the tweets>]",
    "_start_time_": "(string) <date in ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ) of the earliest time from which the tweets can be>",
    "_end_time_": "(string) <date in ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ) of the latest time from which the tweets can be>"
  },
  "discovery": {
    "keywords": "(array<string>) [<words closely related to the desired domain>]",
    "tweets_per_user": "(int) <maximum number of tweets to try to extract from each user (includes tweets, replies, quote tweets and retweets)>"
  },
  "extraction": {
    "_person_": "(boolean) <extract person entities from selected websites>",
    "_norp_": "(boolean) <extract nationalities, religious or political group entities from selected websites>",
    "_fac_": "(boolean) <extract buildings and other man made structures from selected websites>",
    "_organization_": "(boolean) <extract organization entities from selected websites>", 
    "_location_": "(boolean) <extract country, state and city from selected websites>",
    "_places_": "(boolean) <extract other locations and landmarks from selected websites>",
    "_product_": "(boolean) <extract object entities from selected websites>",
    "_event_": "(boolean) <extract natural and human events from selected websites>",
    "_art_": "(boolean) <extract art entities from selected websites>",
    "_law_": "(boolean) <extract law documents from selected websites>",
    "_language_": "(boolean) <extract language entities from selected websites>",
    "_date_": "(boolean) <extract absolute/relative dates and periods from selected websites>",
    "_time_": "(boolean) <extract times smaller than a day from selected websites>",
    "_percent_": "(boolean) <extract percentages from selected websites>",
    "_money_": "(boolean) <extract monetary values from selected websites>",
    "_quantity_": "(boolean) <extract measurements from selected websites>",
    "_ordinal_": "(boolean) <extract ordinal numbers from selected websites>",
    "_cardinal_": "(boolean) <extract all other numerals from selected websites>"
  }
}
```

 > All parameters between underscores (e.g. `_<param>_`) are optional.

### Running

To run the application use the following command:

```bash
spark-submit --driver-memory 4G --executor-memory 4G --conf spark.local.dir=/home/tgrine/tmp main.py
```