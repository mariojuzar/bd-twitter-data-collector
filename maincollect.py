import csv
import json
import re
import time
from twython import *
from datetime import datetime
from keyhandler import listAPI

# store max list of API stored
maxLAPI = len(listAPI)

idx = 0
api = listAPI[idx]

initial_screen_name = 'tfitb'
user_file = 'user.csv'
follower_file = 'follow.csv'
tweet_file = 'tweet.csv'
json_file = 'data2.json'

users = []
rels = []
tweets = []


def limit_handling():
    global idx, maxLAPI, api
    idx += 1

    if idx >= maxLAPI:
        reset = float(api.get_lastfunction_header(header='x-rate-limit-reset'))
        idx = 0

    api = listAPI[idx]

    if idx == 0:
        restime = datetime.fromtimestamp(reset)
        now = datetime.now()
        diff = restime - now
        sec = diff.seconds
        if 0 < sec < 950:
            print(now)
            print("search suspend for " + str(sec) + " seconds")
            time.sleep(sec)


def remove_emoji(string):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "] + ", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)


start = datetime.now()
print(start)

print("start to get all follower from initial user")
cursor = -1

while cursor != 0:
    try:
        followers = api.get_followers_list(id=initial_screen_name, cursor=cursor)
        if followers:
            for follower in followers['users']:
                if not follower['protected']:
                    user = {}

                    user['id'] = follower['id']
                    user['name'] = follower['name']
                    user['screen_name'] = follower['screen_name']
                    user['created_at'] = follower['created_at']
                    user['followers_count'] = follower['followers_count']
                    user['friends_count'] = follower['friends_count']

                    users.append(user)

        cursor = followers['next_cursor']

    except TwythonRateLimitError:
        limit_handling()
        continue

print("follower from initial user done")

""""
with open('data.json') as json_data:
    d = json.load(json_data)
    users = d['users']
    rels = d['rels']
"""

print("starting getting all tweets from user lv 1")

for u in users:
    while True:
        try:
            tweets_user = api.get_user_timeline(id=u['id'], count=50)
            for tweet in tweets_user:
                tw = {}
                tw['id'] = tweet['id']
                tw['created_at'] = tweet['created_at']
                tw['id_user'] = tweet['user']['id']

                hashtag = []
                if 'hashtags' in tweet['entities']:
                    for h in tweet['entities']['hashtags']:
                        hashtag.append(h['text'])
                user_mention = []
                if 'user_mentions' in tweet['entities']:
                    for um in tweet['entities']['user_mentions']:
                        user_mention.append(um['id'])

                tw['hashtag'] = hashtag
                tw['user_mention'] = user_mention

                tw['favorite_count'] = tweet['favorite_count']
                tw['retweet_count'] = tweet['retweet_count']
                tw['text'] = remove_emoji(tweet['text'])
                tw['in_reply_to_status_id'] = tweet['in_reply_to_status_id']
                tw['in_reply_to_user_id'] = tweet['in_reply_to_user_id']
                tw['is_quote_status'] = tweet['is_quote_status']
                if 'quoted_status' in tweet:
                    tw['quoted_status_id'] = tweet['quoted_status']['id']
                    tw['quoted_user_id'] = tweet['quoted_status']['user']['id']
                else:
                    tw['quoted_status_id'] = None
                    tw['quoted_user_id'] = None

                if 'retweeted_status' in tweet:
                    tw['retweeted_status'] = tweet['retweeted_status']['id']
                    tw['retweeted_user'] = tweet['retweeted_status']['user']['id']
                else:
                    tw['retweeted_status'] = None
                    tw['retweeted_user'] = None

                if tw['in_reply_to_status_id'] is not None:
                    tw['type'] = 'REPLY'
                elif tw['is_quote_status']:
                    tw['type'] = 'QUOTED'
                elif tw['retweeted_status'] is not None:
                    tw['type'] = 'RETWEET'
                else:
                    tw['type'] = 'TWEET'

                tweets.append(tw)

            break

        except TwythonRateLimitError:
            limit_handling()
            continue

        except TwythonError as e:
            print(e)
            if '401 (Unauthorized)' in e.args[0]:
                break
            else:
                limit_handling()
            continue


print("done getting all tweet from user lv 1")

print("starting getting all follower from user lv 1")


for u in users:
    while True:
        try:
            follower_ids = api.get_followers_ids(id=u['id'], count=1250)
            for ids in follower_ids['ids']:
                r = {}
                r['id_user'] = u['id']
                r['id_follower'] = ids
                if r not in rels:
                    rels.append(r)

            break

        except TwythonRateLimitError:
            limit_handling()
            continue

        except TwythonError as e:
            print(e)
            limit_handling()
            continue

print("done getting all follower from user lv 1")

print("starting getting all following from user lv 1")

for u in users:
    while True:
        try:
            follower_ids = api.get_friends_ids(id=u['id'], count=125)
            for ids in follower_ids['ids']:
                r = {}
                r['id_user'] = u['id']
                r['id_follower'] = ids
                if r not in rels:
                    rels.append(r)
            break

        except TwythonRateLimitError:
            limit_handling()
            continue

        except TwythonError as e:
            print(e)
            limit_handling()
            continue


print("done getting all following from user lv 1")

#save all data to json
with open(json_file, 'w') as jsonfile:
    json.dump({'users': users, 'rels': rels, 'tweet': tweets}, jsonfile, default=str)


print("done make json")
print("total users : "+str(len(users)))
print("total rels : "+str(len(rels)))
print("total tweets : "+str(len(tweets)))

end = datetime.now()
print(end)
print(end-start)
