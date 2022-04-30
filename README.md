# Thesis_Project

### Input

To configure the inputs, a file with the name `config.json` should be in the projects directory and have the following
structure.

```json
{
  "searching": {
    "users": <number of users to try to collect from the tweet search>,
    "keywords": [<words to search for in tweets>],
    "hashtags": [<hashtags to search for in tweets>],
    "exclude"*: [<words that can not appear in tweets>],
    "countries"*: [<ISO codes of countries to accept tweets from>],
    "languages"*: [<BCP 47 identifiers of languages accepted for the tweets>],
    "start_time"*: <date in ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ) of the earliest time from which the tweets can be>
    "end_time"*: <date in ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ) of the latest time from which the tweets can be>
  },
  "discovery": {
    "keywords": [<words closely related to the desired domain>],
    "tweets_per_user": <maximum number of tweets to try to extract from each user (includes tweets, replies, quote tweets and retweets)>
  },
  "extraction": {
    "person"*:        (boolean) <extract person entities from selected websites>,
    "norp"*:          (boolean) <extract nationalities, religious or political group entities from selected websites>,
    "fac"*:           (boolean) <extract buildings and other man made structures from selected websites>,
    "organization"*:  (boolean) <extract organization entities from selected websites>, 
    "location"*:      (boolean) <extract country, state and city from selected websites>,
    "places"*:        (boolean) <extract other locations and landmarks from selected websites>,
    "product"*:       (boolean) <extract object entities from selected websites>,
    "event"*:         (boolean) <extract natural and human events from selected websites>,
    "art"*:           (boolean) <extract art entities from selected websites>,
    "law"*:           (boolean) <extract law documents from selected websites>,
    "language"*:      (boolean) <extract language entities from selected websites>,
    "date"*:          (boolean) <extract absolute/relative dates and periods from selected websites>,
    "time"*:          (boolean) <extract times smaller than a day from selected websites>,
    "percent"*:       (boolean) <extract percentages from selected websites>,
    "money"*:         (boolean) <extract monetary values from selected websites>,
    "quantity"*:      (boolean) <extract measurements from selected websites>,
    "ordinal"*:       (boolean) <extract ordinal numbers from selected websites>,
    "cardinal"*:      (boolean) <extract all other numerals from selected websites>,
  }
}
```

 > All parameters marked with `*` are optional.

