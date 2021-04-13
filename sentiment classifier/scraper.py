import requests
import shutil
from pymongo import MongoClient
import csv
import datetime
import urllib3
import pprint
import pytz
import twint
import re
import spacy
from nltk.corpus import stopwords
import en_vectors_web_lg
import os
from bson.son import SON
import pprint

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


def testMongo(collectionName):
    """ Use either tracksCollection or tweetsCollection2 """
    client = MongoClient('mongodb://127.0.0.1:27017/')
    db = client["spotifyDatabase"]
    collection = db[collectionName]
    return collection


def spotifyConnectionToken():
    """returns the Spotify Authentication token, in the correct header format"""
    CLIENT_ID = '347403518d6243bbbdcb5aac9aee1684'                   # Dont commit these to github!!
    CLIENT_SECRET = '28c25ebbaf3f4cca87cda9edfae6a434'

    AUTH_URL = 'https://accounts.spotify.com/api/token'

    auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    })

    # convert the response to JSON
    auth_response_data = auth_response.json()

    # save the access token
    access_token = auth_response_data['access_token']
    headers = {'Authorization': 'Bearer {token}'.format(token=access_token)}

    return headers

def totalStreamsDay(artist, day):
    """Mongo Aggregation that returns the total streams for a given artist on a given day.
    :artist: The name of the artist as seen in the chart. Eg. "Post Malone", "Halsey" etc
    :day: The date for the single chart as a string. Eg. "2019-01-03"
    """
    mongodb = testMongo("tracksDatabase")
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
    mongodb = testMongo("tracksDatabase")
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
    mongodb = testMongo("tracksCollection")
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
    mongodb = testMongo("tracksCollection")
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
    mongodb = testMongo("tracksCollection")
    return len(mongodb.tracksCollection.distinct("title"))


def getTweetRange(artist):
    mongodb = testMongo("tweetsCollection2")
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
    mongodb = testMongo("tracksCollection")
    return len(mongodb.distinct("artist"))


def getAllArtists():
    mongodb = testMongo("tracksCollection")
    #tracks = mongodb["tracksCollection"]
    artists = mongodb.distinct("artist")
    return artists


def getArtistId(artistName):
    """Get the MongoDb ID for a given artist"""

    mongodb = testMongo("tracksCollection")
    pipeline = [
        {"$match": {"artist": artistName}}
        #{"$project": {"_id": 1}}

    ]
    print(list(mongodb.aggregate(pipeline)))


def getSpotifyId(artistName):
    """Get the Spotify ID for a given artist"""

    mongodb = testMongo("artistCollection")
    pipeline = [
        {"$match": {"name": artistName}},
        {"$project": {"spotifyId": 1}}
    ]
    result = list(mongodb.aggregate(pipeline))
    return result[0]["spotifyId"]


def getArtistReleases(artistName):
    """Returns all the releases for a given artist"""
    mongodb = testMongo("artistCollection")
    pipeline = [
        {"$match": {"name": artistName}},
        {"$project": {"releases": 1}}
    ]
    result = list(mongodb.aggregate(pipeline))
    if "releases" in result[0]:
        return result[0]["releases"]
    else:
        return []


def getArtistFollowers():
    """Returns all the follower counts for all artists"""
    mongodb = testMongo("artistCollection2")
    pipeline = [
        {"$project": {"name": 1, "followers": 1}},
        {"$sort": { "name": -1 } }
    ]
    result = list(mongodb.aggregate(pipeline))
    return result


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


def createArtistCollection():
    """This builds the intial artistCollection in Mongo- containing artist name, genres and their spotify ID. """
    mongodb = testMongo("artistCollection2")
    allArtists = getAllArtists()

    spotify_access_header = spotifyConnectionToken()

    for idx, artist in enumerate(allArtists):
        
        if "&" in artist: 
                artistName = artist.replace("&", "") # API will exclude any part of an artists name that comes after a '&' in a search- which is bad.
        else:
            artistName = artist

        artist_object = requests.get(f"https://api.spotify.com/v1/search?q={artist}&type=artist", headers=spotify_access_header).json() #&market=US ??
        bestIdx = 0 # Uses the first result by default.
        for idx, result in enumerate(artist_object["artists"]["items"]):
            #print("Current best followers = ", artist_object["artists"]["items"][bestIdx]["followers"]["total"])
            #print("Current follower contender: ", result["followers"]["total"], " with name: ", result["name"])
            if result["followers"]["total"] > artist_object["artists"]["items"][bestIdx]["followers"]["total"] and result["name"] == artist: #Attempts to get the most popular artist that has a matching name (best assumption that it is the correct artist.)
                print("Idx changed: ", idx)
                bestIdx = idx                               #followers is the max, and the name is EXACTLY the same as the artist, we use that one.

        bestObject = artist_object["artists"]["items"][bestIdx]
        #print("'Object' picked: ")
        #print(bestObject)
        
        genres = bestObject["genres"]
        spotifyId = bestObject["id"]
        followers = bestObject["followers"]["total"]
        artistId = bestObject["id"]
        document = {"name": artist, "genres": genres, "spotifyId": artistId, "followers": followers}
        print(idx, ": Going into database: ", document)
        update_result = mongodb.insert_one(
                document
                )
        #print(idx, ". Added artist: ", artist, " to Database.")



def addToArtistCollection():
    """Used this to add the follower count to the artists"""
    
    mongodb = testMongo("artistCollection2")
    allArtists = getAllArtists()

    spotify_access_header = spotifyConnectionToken()

    for idx, artist in enumerate(allArtists):
            if "&" in artist: 
                artistName = artist.replace("&", "")
            else:
                artistName = artist

            print("Adding follower count for: ", artist)
            artist_object = requests.get(f"https://api.spotify.com/v1/search?q={artistName}&type=artist", headers=spotify_access_header).json()
            print(artist_object)
            followerCount = artist_object['artists']['items'][0]['followers']['total']
            update_result = mongodb.update_one({ 
                        "name": artist},{ 
                        "$set": {
                            "followers": followerCount
                        }
                        }, upsert=False)
            print(update_result)
            break
            

        
def addReleases():
    """Adds all releases by artists that were released between 2019-2021"""
    mongodb = testMongo("artistCollection2")
    allArtists = getAllArtists()

    spotify_access_header = spotifyConnectionToken()

    #for idx,artist in enumerate(allArtists):
    #artist = "Post Malone" For testing
    for artist_index, artist in enumerate(allArtists):

        spotifyId = getSpotifyId(artist)
        artist_releases_object = requests.get(f"https://api.spotify.com/v1/artists/{spotifyId}/albums?offset=0&include_groups=album,single&market=US", headers=spotify_access_header).json()
        #pprint.pprint(artist_releases_object)
        albums = artist_releases_object["items"]
        #print(albums)
        release_count = 0
        skipped_count = 0
        failed_count = 0
        added_releases = []
        #print(albums)
        for album in albums:
            #print(album)
            release = {"releaseName": album["name"], "releaseDate": album["release_date"], "type": album["type"], "spotifyId": album["id"]}
            try:
                release_date =  datetime.datetime.strptime(release["releaseDate"], "%Y-%m-%d")
                if release_date > datetime.datetime(2019, 1, 1) and release_date < datetime.datetime(2021, 1, 1) and release["releaseName"] not in added_releases: # Not interested in releases that were not published outside of our timeframe.
                    update_result = mongodb.update_one({ 
                        "name": artist},{ 
                        "$push": {
                            "releases": release
                        }
                        }, upsert=False)
                    
                    release_count += 1
                    added_releases.append(release["releaseName"])
                    
                else:
                    skipped_count +=1
            except ValueError as e:
                print("ValueError exception")
                print(e)
                pass # If the Date is not in the form Y-M-D im not really interested- just having the year for example, isnt helpful in my analysis.
        print(str(artist_index+ 1),  ": Finished added ", str(release_count), " to the database for artist: ", artist, ". ", str(skipped_count), " releases were skipped. There were ", str(failed_count), " failures.")
    # Looks ready for the full loop. Post Malone Test added to Notion.



# This is basically ready to run imo. Too tired to fix any more issues that may come up now ffs hahah



if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    #testMongo()
    #collectCsv()
    #totalStreamsDay("Post Malone", "2019-01-01")
    #bestArtistPosition("DJ Snake", "2019-01-01")
    #bestArtistPositionRange("Post Malone", "2019-01-01", "2019-01-02")
    #twintTest()
    #artists = getAllArtists()
    #for idx, artist in enumerate(artists):
    #    print(idx, " ", artist) 
    #getTweetRange("BANNERS")
    #getAllTweetRanges()
    #mongodb.tracksCollection.update_one({"title":row[1], "artist":row[2]}, {"$setOnInsert": {"title":row[1], "artist":row[2]}, "$push": {"chartPositions": row[0], "chartStreams": row[3], "chartdates": date}}, upsert=True)

    #getArtistGenres()
    #getArtistId("Post Malone")

    #createArtistCollection()

    #getSpotifyId("Post Malone")
    #addReleases()

    #print(getArtistReleases("*NSYNC"))

    #addToArtistCollection()

    print(getArtistFollowers())

#db.tracksCollection.aggregate([ { $match: {artist: "Post Malone", chart.date: "2019-01-01"}}])


# 2892 songs
# 