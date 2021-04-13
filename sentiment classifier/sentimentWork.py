import matplotlib
import matplotlib.pyplot as plt
from pymongo import MongoClient
import datetime
import matplotlib.dates as dates
from scraper import *

def getMongo(collectionName):
    """ Use either tracksCollection or tweetsCollection2 """
    client = MongoClient('mongodb://127.0.0.1:27017/')
    db = client["spotifyDatabase"]
    collection = db[collectionName]
    return collection


def averageSentimentRange(artist, startDay, endDay):
    """Mongo aggregation that sums all the streams for a certain artist over a period in time. range includes both the start and end days of the range.
    :artist: The name of the artist as seen in the chart.Eg. "Post Malone", "Halsey" etc.
    :startDay: The first date included in the range.
    :endDay: The last date included in the range.
    """
    mongodb = getMongo("tweetsCollection2")
    
    if type(startDay) == str or type(endDay) == str: 
        startDay = datetime.datetime.strptime(startDay, "%Y-%m-%d")
        endDay = datetime.datetime.strptime(endDay, "%Y-%m-%d")


    pipeline = [
        {"$match": {"subject": artist, "Date": {"$gt" : startDay, "$lte" : endDay}} },
        
        {"$project": {
            "artist": 1, 
            "sentiment": {"$toInt": "$sentiment"},
            "Date": 1
        }},
        
        {"$group":{"_id": "$artist", "avgSentiment": {"$avg": "$sentiment"} } },
        {"$sort": {"_id": 1}}
    ]

    return list(mongodb.aggregate(pipeline))
    """
    print(type(result))
    print(len(result))
    print(result[0])
    print(type(result[0]))
    print(result[0]["avgSentiment"])
    #print ("HERE: ", result['avgSentiment'])
    
    if len(result) > 0 :
        return result[0]["avgSentiment"]
    else:
        return None
    return list(mongodb.tweetsCollection2.aggregate(pipeline))
    """


def averageSentimentAll():
    """returns a list of all the artists - ranked by their average sentiment across the entire timeframe."""

    mongodb = getMongo("tweetsCollection2")

    pipeline = [
        {"$project": {
            "subject": 1, 
            "sentiment": {"$toInt": "$sentiment"},
            "Date": 1
        }},
        
        {"$group":{"_id": "$subject", "avgSentiment": {"$avg": "$sentiment"} } },
        {"$sort": {"avgSentiment": 1}}
    ]

    results = list(mongodb.aggregate(pipeline))

    returnDict = {}
    for idx, result in enumerate(results):
        #print(idx+1, ": Artist: ", result["_id"], " Avg. Sentiment: ", result["avgSentiment"])
        returnDict[result["_id"]] = result["avgSentiment"]
    return returnDict


def totalStreamsAll():
    """returns a list of all the artists- ranked by their total spotify stream count."""

    mongodb = getMongo("tracksCollection")

    pipeline = [
        {"$unwind": "$chart"},
        {"$group":{"_id": "$artist", "totalStreams": {"$sum": "$chart.chartStreams"} } },
        {"$sort": {"totalStreams": -1}}
    ]

    results = list(mongodb.aggregate(pipeline))
    #print(results)

    returnDict = {}
    for idx, result in enumerate(results):
        #print(idx+1, ": Artist: ", result["_id"], " Total Streams: ", result["totalStreams"])
        returnDict[result["_id"]] = result["totalStreams"]
    return returnDict


def totalTrackStreams(artistName, trackName):
    """Returns the total streams for a single track by a certain artist. """
    mongodb = getMongo("tracksCollection")

    pipeline = [
        {"$match": {"artist": artistName, "title": trackName} },
        {"$unwind": "$chart"}#,
        #{"$group":{"_id": "$title", "totalStreams": {"$sum": "$chart.chartStreams"} } }
    ]
    results = list(mongodb.aggregate(pipeline))
    if len(results) > 0:
        return results[0]["chart"]["chartStreams"]

def plotSentimentStreams():
    """Plots a graph comparing an artists stream count and their average sentiment"""

    sentiment = averageSentimentAll()
    streams = totalStreamsAll()

    x_values = []
    y_values = []
    for artist in sentiment:
        print(streams[artist], " ", sentiment[artist])
        y_values.append(streams[artist])
        x_values.append(sentiment[artist])

    plt.title("Graph showing the average collected sentiment of artists, and their spotify stream count.")
    plt.ylabel("Stream Count")
    plt.xlabel("Avg. Sentiment")
    plt.xlim(0, 4)
    plt.plot(x_values, y_values, 'o')
    plt.show()


    

def getWeekdays(startDate, endDate):
    startDay = datetime.datetime.strptime(startDate, "%Y-%m-%d")
    endDay = datetime.datetime.strptime(endDate, "%Y-%m-%d")
    dates = []
    currentDate = startDay
    
    while currentDate <= endDay:
        dates.append(currentDate)
        currentDate += datetime.timedelta(days = 7)

    return dates



def fullSentimentChart(artist):
    """Produces a full matplotlib chart of the given artists sentiment across the entire 2 years worth of data."""

    # x is the time frame
    # y is the sentiment value
    colors = ["red", "green", "blue"]
    x_values = {}
    y_values = {}
    artists = ["Ed Sheeran", "Coldplay", "The Chainsmokers"]
    #print(x_values)
    #for idx, date in enumerate(x_values[:-1]):
    #    y_values.append(averageSentimentRange(artist, x_values[idx], x_values[idx+1] ))
    fig, ax = plt.subplots(1)
    fig.autofmt_xdate()
    plt.title("Sentiment of tweets that are about different Artists")
    plt.xlabel("Dates")
    plt.ylabel("Sentiment")
    plt.ylim(0, 4)
    plt.gca().get_yticklabels()[0].set_color("#FF0000")
    plt.gca().get_yticklabels()[1].set_color("#DC0000")
    plt.gca().get_yticklabels()[2].set_color("#A00000")
    plt.gca().get_yticklabels()[3].set_color("#640000") 
    plt.gca().get_yticklabels()[4].set_color("#006400") 
    plt.gca().get_yticklabels()[5].set_color("#006400")
    plt.gca().get_yticklabels()[6].set_color("#008000")
    plt.gca().get_yticklabels()[7].set_color("#008B00")
    plt.gca().get_yticklabels()[8].set_color("#32BE00")
    
    for idx, artist in enumerate(artists):
        x_values[artist] = []
        y_values[artist] = []
        mongoData = averageSentimentRange(artist, "2019-01-13", "2021-01-01")
    
    
        for i in mongoData:
            #x_values.append(dates.date2num(i["_id"]))
            x_values[artist].append(i["_id"])
            print("Date:", i["_id"], " Date as number: ", dates.date2num(i["_id"]))
            print("\n")
            # _id here is the dates as the Mongo's aggreagation grouped the sentiment by dates.
            y_values[artist].append(i["avgSentiment"])

    
        plt.plot(x_values[artist], y_values[artist], label= artist, color = colors[idx])
    
    #xfmt = mdates.DateFormatter()

    plt.legend()
    

    plt.show()



    #print(x_values)
    #print(y_values)
    #print(y_values)

    #print("X length: ", len(x_values))
    #print("Y length: ", len(y_values))


def releasesSentiment():
    """Go through each release by an artist, and note the sentiment the week before it was released, and the week after, and calculate the % change in sentiment. """
    mongodb_artist = testMongo("artistCollection2")

    allArtists = getAllArtists()
    sentimentList = []
    streamCountList = []
    
    for artist in allArtists:
        print("looking through ", artist, "'s releases.")
        releases = getArtistReleases(artist) # from scraper.py

    # 30 days before, and 30 days after.

        for release in releases:
            releaseDate = release["releaseDate"]
            releaseName = release["releaseName"]

            releaseDateObj = datetime.datetime.strptime(releaseDate, "%Y-%m-%d")
            beforeDate = releaseDateObj - datetime.timedelta(days=30)
            afterDate = releaseDateObj + datetime.timedelta(days=30)

            try:
                beforeSentiment = averageSentimentRange(artist, beforeDate, releaseDateObj)[0]['avgSentiment']
                afterSentiment = averageSentimentRange(artist, releaseDateObj, afterDate)[0]['avgSentiment']
                streamCount = totalTrackStreams(artist, releaseName)


                if beforeSentiment == 0:
                    print("\n")
                    print("beforeSentiment is Zero. Incoming ZeroDivisionError")
                    print("artist: ", artist)
                    print("release: ", release)
                    print("Before Date: ", beforeDate)
                    print("Release Date: ", releaseDate)
                    print("beforeSentiment: ", beforeSentiment)
                    print("afterSentiment: , ", afterSentiment)
                    print("\n")

                if beforeSentiment != 0 and afterSentiment != 0 and streamCount is not None:

                    changeInSentiment = ( (afterSentiment/beforeSentiment) * 100) - 100

                    
                    print("STREAM COUNT: ", streamCount)
                    sentimentList.append(changeInSentiment)
                    streamCountList.append(streamCount)
            
            except IndexError as e:
                # Can happen if there is no sentiment collected from my scraping :(
                print("TypeError")
                print(e)

        


    print("sentimentList Length: ", len(sentimentList))
    print("streams List Length: ", len(streamCountList))

    with open('sentimentChanges2.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for idx, line in enumerate(sentimentList):
                writer.writerow([line, streamCountList[idx]])


def sentimentChangeChart():
    with open("sentimentChanges2.csv", 'r', encoding="utf8") as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=','))
        
        y_values = [float(i[0]) for i in csv_reader]
        x_values = [float(i[1]) for i in csv_reader]

        bigChangeCount = 0
        bigStreamCount = 0
        bigStreamSentiment = []

        for i in y_values:
            if i > 20 or i < -20:
                bigChangeCount += 1

        for idx, i in enumerate(x_values): 
            if i > 2000000:
                bigStreamCount +=1
                bigStreamSentiment.append(abs(y_values[idx]))

        avgBigStreamSentiment = sum(bigStreamSentiment) /len(bigStreamSentiment)




        print("Number of large swings in sentiment: ", bigChangeCount)
        print("% of tracks that had large swings in sentiment: ", (bigChangeCount/len(y_values) * 100) )

        print("Number of tracks with large stream count: ", bigStreamCount)

        print("Average Sentiment change for those 'large' tracks: ", avgBigStreamSentiment)

        plt.title("Graph showing the sentiment change around a track's release, and its final spotify stream count.")
        #plt.ylabel("Stream Count")
        #plt.xlabel("Sentiment % Change")
        #plt.yticklabels=[]
        #plt.ylim(-100, 100)
        plt.plot(x_values, y_values, 'o')
        plt.show()


def sentimentFollowersChart():
    """Produces a chart showing the amount of followers each artist has, to their average sentiment over 2019-2021 """

    sentiment = averageSentimentAll()
    print("Sentiment count:", len(sentiment))
    print(len(getArtistFollowers()))
    artist_followers = {}
    y_values = [] # followers
    x_values = [] # sentiment
    
    for i in getArtistFollowers():
        if i["name"] != "BANNERS":
            artist_followers[i["name"]] = [i["followers"], sentiment[i["name"]]]
            sentiment_value = sentiment[i["name"]]
            followers = i["followers"]

            x_values.append(sentiment_value)
            y_values.append(followers)


    print("Y length: ", len(y_values))
    print("X length: ", len(x_values))

    print(artist_followers)
    #print("yo")

    plt.title("Graph showing the Relationship between Avg. Sentiment, and Spotify Follower Count")
    plt.xlabel("Avg. Sentiment")
    plt.ylabel("No. of Spotify Followers")
    #plt.yticklabels=[]
    #plt.ylim(-100, 100)
    plt.plot(x_values, y_values, 'o')
    plt.show()
    #print(artist_followers)
    #print(sentiment)









#print(averageSentimentRange("347aidan", "2019-12-05", "2021-01-01"))
#fullSentimentChart("Post Malone")
#averageSentimentAll()
#totalStreamsAll()

#plotSentimentStreams()

#releasesSentiment()

#sentimentChangeChart()
sentimentFollowersChart()

#totalTrackStreams("13 Organisé", "13 Organisé")