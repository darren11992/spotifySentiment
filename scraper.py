import requests
import shutil
from pymongo import MongoClient
import csv
import datetime
import urllib3
import pprint
import pytz
import twint
import csv
import re
import spacy
from nltk.corpus import stopwords
import en_vectors_web_lg
import os
from bson.son import SON

def collectCsv():
    mongodb = testMongo()
    client = MongoClient('mongodb://127.0.0.1:27017/')
    
    date = datetime.datetime(2019, 1, 1)
    date_str = str(date)[0:10]
    
    while date_str != "2021-01-01":
        print("Pinging chart for date: ", date_str)
        url = f"https://spotifycharts.com/regional/global/daily/{date_str}/download"

        r = requests.get(url, verify=False, stream=True)
        if r.status_code != 200:
            print("request failed")
            print(r.status_code)
            break
        decoded_csv = r.content.decode('utf-8')
        read_csv = csv.reader(decoded_csv.splitlines(), delimiter=',')
        csv_list = list(read_csv)
        for row in csv_list[2:]: # start from 2nd row, everything before is headers.
            artist = row[2]
            song = row[1]
            mongodb.tracksCollection.update_one({
                "title":row[1], 
                "artist":row[2]}, 
                {"$setOnInsert": {
                    "title":row[1],
                    "artist":row[2]
                },
                "$push": { 
                    "chart":{
                        "date": date,
                        "chartPositions": int(row[0]),
                        "chartStreams": int(row[3])
                    }
                }
                }, upsert=True)
        date += datetime.timedelta(days=1)
        date_str = str(date)[0:10]


def testMongo():
    client = MongoClient('mongodb://127.0.0.1:27017/')
    db = client["spotifyDatabase"]
    return db

def totalStreamsDay(artist, day):
    """Mongo Aggregation that returns the total streams for a given artist on a given day.
    :artist: The name of the artist as seen in the chart. Eg. "Post Malone", "Halsey" etc
    :day: The date for the single chart as a string. Eg. "2019-01-03"
    """
    mongodb = testMongo()
    day = datetime.datetime.strptime(day, "%Y-%m-%d")
    pipeline = [
        {"$match": {"artist": artist}},
        {"$unwind": "$chart"},
        {"$match": {"chart.date": day}},
        {"$group":{"_id": "$artist", "totalStreams": {"$sum": "$chart.chartStreams"} } }
    ]
    print(list(mongodb.tracksCollection.aggregate(pipeline)))

def bestArtistPosition(artist, day):
    """Mongo Aggregation that returns a given artists best position for a given date.
    :artist: The name of the artist as seen in the chart. Eg. "Post Malone", "Halsey" etc
    :day: The date for the single chart as a string. Eg. "2019-01-03"
    """
    mongodb = testMongo()
    day = datetime.datetime.strptime(day, "%Y-%m-%d")
    pipeline = [
        {"$match": {"artist": artist} },
        {"$unwind": "$chart"},
        {"$match": {"chart.date": day}},
        {"$group":{"_id": "$chart.chartPositions" } },
        {"$sort": { "_id": 1 } }, 
        {"$limit": 1 }
        #{"$group":{"_id": "$artist", "totalStreams": {"$sum": "$chart.chartStreams"} } }
    ]
    print(list(mongodb.tracksCollection.aggregate(pipeline)))


def bestArtistPositionRange(artist, startDay, endDay):
    """Mongo Aggregation that returns the best position for a given artist, each day over a certain time frame.
    :artist: The name of the artist as seen in the chart.Eg. "Post Malone", "Halsey" etc.
    :startDay: The first date included in the range.
    :endDay: The last date included in the range.
    """
    mongodb = testMongo()
    startDay = datetime.datetime.strptime(startDay, "%Y-%m-%d")
    endDay = datetime.datetime.strptime(endDay, "%Y-%m-%d")
    pipeline = [
        {"$match": {"artist": artist} },
        {"$project": {
            "artist": 1, 
            "title": 1,
            "chart": {
                "$filter":{
                    "input": "$chart",
                    "as": "chart",
                    "cond": { "$and": [
                        {"$gte": ["$$chart.date", startDay] }, 
                        {"$lte": ["$$chart.date", endDay] }
                    ]}
                }
            },  
        }}
        #{"$project": {
        #    "artist": 1,
        #    "chart.date": 1,
        #    "chart.chartPositions": 1

        #}}
    ]
    result = list(mongodb.tracksCollection.aggregate(pipeline))[0]
    print(result)
    for i in result["chart"]:
        print(i["date"], i["chartPositions"])

def totalStreamsRange(artist, startDay, endDay):
    """Mongo aggregation that sums all the streams for a certain artist over a period in time. range includes both the start and end days of the range.
    :artist: The name of the artist as seen in the chart.Eg. "Post Malone", "Halsey" etc.
    :startDay: The first date included in the range.
    :endDay: The last date included in the range.
    """
    mongodb = testMongo()
    startDay = datetime.datetime.strptime(startDay, "%Y-%m-%d")
    endDay = datetime.datetime.strptime(endDay, "%Y-%m-%d")
    pipeline = [
        {"$match": {"artist": artist} },
        {"$project": {
            "artist": 1, 
            "chart": {
                "$filter":{
                    "input": "$chart",
                    "as": "chart",
                    "cond": { "$and": [
                        {"$gte": ["$$chart.date", startDay] }, 
                        {"$lte": ["$$chart.date", endDay] }
                    ]}
                }
            }  
        }},
        {"$unwind": "$chart"},
        {"$group":{"_id": "$artist", "totalStreams": {"$sum": "$chart.chartStreams"} } }
        #{"$group":{"_id": None, "totalStreams": {"$sum": "$chart.chartStreams"} } }

    ]
    print(list(mongodb.tracksCollection.aggregate(pipeline)))

def getTotalSongs():
    mongodb = testMongo()
    return len(mongodb.tracksCollection.distinct("title"))


def getTweetRange(artist):
    mongodb = testMongo()
    pipeline = [
        {"$match": {"subject": artist}},
        {"$sort": SON([("Date", 1)])},
        {"$group":{"_id": "$subject", "firstTweet": {"$first": "$$ROOT"}, "lastTweet": {"$last": "$$ROOT"}}}
    ]
    result = list(mongodb.tweetsCollection2.aggregate(pipeline))
    print(result)
    firstDate = result[0]["firstTweet"]["Date"]
    lastDate = result[0]["lastTweet"]["Date"]
    return (lastDate - firstDate).days

    #Note: BANNERS is breaking this. Handle the exception, or remove him from the Spotify Collection
    

def getAllTweetRanges():
    artistList = getAllArtists()
    with open('tweetTimes.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for artist in artistList:
            if artist != "BANNERS":
                print("Current artist: ", artist)
                timeRange = getTweetRange(artist)   
                writer.writerow([artist, timeRange])





def getTotalArtists():
    mongodb = testMongo()
    return len(mongodb.tracksCollection.distinct("artist"))


def getAllArtists():
    mongodb = testMongo()
    tracks = mongodb["tracksCollection"]
    artists = tracks.distinct("artist")
    return artists

def incrementDates(sinceDate, untilDate):
    untilDate = datetime.datetime.strptime(untilDate, "%Y-%m-%d")
    sinceDate = untilDate + datetime.timedelta(days=1)
    untilDate += datetime.timedelta(weeks=2, days=1)
    sinceDate = str(sinceDate)[0:10]
    untilDate = str(untilDate)[0:10]
    return sinceDate, untilDate
    

def twintTest():
    
    mongodb = testMongo()
    artistList = getAllArtists()
    print(len(artistList))
    startDate = "2019-01-01"
    finishDate = "2021-01-01"

    
    c = twint.Config()
    #c.Username = "elonmusk"
    #c.Search = "Harry Styles" <---
    c.Store_csv = True
    c.Lang = "en"
    c.Hide_output = True
    c.Email = False
    c.Phone = False
    c.Output = "twint3.csv"
    c.Limit = 50
    c.Count = True
    stopwords_list = set(stopwords.words("english"))
    
    for artist in artistList[734:]:
        print("Searching tweets for: ", artist)
        c.Search = artist
        cleaned_artist_name = re.sub('[^a-zA-Z\s]','', artist)
        c.Output = f"twint-{cleaned_artist_name}.csv"
        currentSinceDate = startDate
        currentUntilDate = "2019-01-14"
        while datetime.datetime.strptime(currentSinceDate, "%Y-%m-%d") < datetime.datetime.strptime(finishDate, "%Y-%m-%d"):
            c.Since = currentSinceDate
            c.Until = currentUntilDate
            print("Searching for artist: ", artist, " between the dates: ", currentSinceDate, " and ", currentUntilDate)
            twint.run.Search(c)
            currentSinceDate, currentUntilDate = incrementDates(currentSinceDate, currentUntilDate)


        with open(f'twint-{cleaned_artist_name}.csv', 'r', encoding="utf8") as csv_file:
            csv_reader = list(csv.reader(csv_file, delimiter=','))
        for row in csv_reader[2:]: # start from 2nd row, everything before is headers.
                subject = artist
                song = row[1]
                #print("Subject: ", subject, "Tweet: ", row[10], "Date: ", datetime.datetime.strptime(row[3], "%Y-%m-%d"))
                tweet = row[10].lower()
                cleaned_tweet = re.sub("[^a-z\s]","", tweet)
                #print("Cleaned Tweet: ", cleaned_tweet)
                
                tweet_no_stopwords = " ".join([i for i in cleaned_tweet.split() if i not in stopwords_list])
                tweet_no_links = " ".join([i for i in tweet_no_stopwords.split() if "http" not in i])
                #print("Tweet with Stopwords removed: ", tweet_no_stopwords)
                mongodb.tweetsCollection2.insert_one({
                    "subject": subject, 
                    "text": tweet_no_links,
                    "Date": datetime.datetime.strptime(row[3], "%Y-%m-%d")})

        os.remove(f"twint-{cleaned_artist_name}.csv")
        
            
        """
        nlp = en_vectors_web_lg.load()
        tweet_doc = nlp(tweet_no_stopwords)
        print("tweet_doc: ", tweet_doc)
        print("Token: ")
        for token in tweet_doc:
            print(token.text)
        print(tweet_doc.vector)
        print("\n")
        """
        """
        mongodb.tweetsCollection.insert_one({
            "subject": subject, 
            "text": tweet_no_stopwords,
            "Date": datetime.datetime.strptime(row[3], "%Y-%m-%d")})
        """


if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    testMongo()
    #collectCsv()
    #totalStreamsDay("Post Malone", "2019-01-01")
    #bestArtistPosition("DJ Snake", "2019-01-01")
    #bestArtistPositionRange("Post Malone", "2019-01-01", "2019-01-02")
    #twintTest()
    #artists = getAllArtists()
    #for idx, artist in enumerate(artists):
    #    print(idx, " ", artist) 
    #getTweetRange("BANNERS")
    getAllTweetRanges()
    #mongodb.tracksCollection.update_one({"title":row[1], "artist":row[2]}, {"$setOnInsert": {"title":row[1], "artist":row[2]}, "$push": {"chartPositions": row[0], "chartStreams": row[3], "chartdates": date}}, upsert=True)









#db.tracksCollection.aggregate([ { $match: {artist: "Post Malone", chart.date: "2019-01-01"}}])


# 2892 songs
# 