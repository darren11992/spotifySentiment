import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB, BernoulliNB
from sklearn.metrics import accuracy_score
from sklearn import preprocessing
import random
import spacy
import csv
import nltk
from nltk.corpus import stopwords
import re
import pickle
import matplotlib.pyplot as plt 
from sklearn.metrics import plot_confusion_matrix, confusion_matrix
from pymongo import MongoClient
from bson.objectid import ObjectId



# Sentiment values in dataset:
    # 0 = negative
    # 2 = neutral
    # 4 = positive


def trainTestSplit():
    data = pd.read_csv('twitterSentiment.csv')

    tweets = data["text"]
    sentiment = data["sentiment"]

    x_train, x_test, y_train, y_test = train_test_split(tweets, sentiment, test_size=0.2, shuffle=True)

    x_train.to_csv('x_train.csv', index = False)
    x_test.to_csv('x_test.csv', index = False)
    y_train.to_csv('y_train.csv', index = False)
    y_test.to_csv('y_test.csv', index = False)

def open_csv(csv_file):
    with open(csv_file, 'r', encoding="utf8") as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=','))
        fileList = [x[0] for x in csv_reader]
    return fileList


def tokenizer(doc):
    # Using default pattern from CountVectorizer
    token_pattern = re.compile('(?u)\\b\\w\\w+\\b')
    return [t for t in token_pattern.findall(doc)]


def get_vectorizer():

    with open("twitterSentiment.csv", 'r', encoding="utf8") as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=','))
        full_x = [x[5] for x in csv_reader]

    stop_words = set(stopwords.words('english')) # Whatever you want to have as stop words.
    vocabulary = set([word for doc in full_x for word in tokenizer(doc) if word not in stop_words])


    vectorizer = CountVectorizer(
        analyzer = 'word',
        lowercase = False,
        vocabulary = vocabulary
    )

    return vectorizer

def text_classifier():
    
    data = []
    data_labels = []
    
    
    #naive_bayes_classifier = GaussianNB() #naiveBayes1.pkl
    naive_bayes_classifier = BernoulliNB(alpha=0.8) #naiveBayes2.pkl

    full_x_train = open_csv("x_train.csv")[1:]
    full_y_train = open_csv("y_train.csv")[1:]

    #full_x = open_csv("twitterSentiment.csv")
    with open("twitterSentiment.csv", 'r', encoding="utf8") as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=','))
        full_x = [x[5] for x in csv_reader]

    print("full x: ", len(full_x))
    #print(full_x)

    full_x_test = open_csv("x_test.csv")
    full_y_test = open_csv("y_test.csv")    
    print(len(full_x_train))
    print(len(full_y_train))


    stop_words = set(stopwords.words('english')) # Whatever you want to have as stop words.
    vocabulary = set([word for doc in full_x for word in tokenizer(doc) if word not in stop_words])

    print("vocab: ", len(vocabulary))

    vectorizer = CountVectorizer(
        analyzer = 'word',
        lowercase = False,
        vocabulary = vocabulary
    )

    chunk_size = 1000
    current_chunk_start = 0
    
    while (current_chunk_start) != len(full_x_train):
        print("Start: ", current_chunk_start)
        current_chunk_finish = current_chunk_start + chunk_size
        print("Finish: ", current_chunk_start + chunk_size)
        print("\n")

        current_x_chunk = full_x_train[current_chunk_start:current_chunk_finish]
        current_y_chunk = full_y_train[current_chunk_start:current_chunk_finish]


        #Spiceing incorrectly? Should have have same column count each time???....

        
        current_chunk_vector = vectorizer.transform(current_x_chunk)
        #print("length after fit_transform: ", current_chunk_vector.getnnz())
        #current_chunk_vector = current_chunk_vector.reshape(-1, 1)
        #print("length after reshape: ", current_chunk_vector.getnnz())
        current_chunk_vector = current_chunk_vector.toarray()
        print("length after toarray: ", len(current_chunk_vector))
        naive_bayes_classifier.partial_fit(current_chunk_vector, current_y_chunk, classes=["0", "2", "4"])
        current_chunk_start += chunk_size

    model_name = "naiveBayes3.pkl"
    with open(model_name, 'wb') as file:
        pickle.dump(naive_bayes_classifier, file)
    
    x_test_vector = vectorizer.fit_transform(full_x_test)


def load_model(model_name):
    with open(model_name, 'rb') as file:
        naive_bayes_classifier = pickle.load(file)
    return naive_bayes_classifier


def test_model(model_name):

    vectorizer = get_vectorizer()
    full_x_test = open_csv("x_test.csv")
    full_y_test = open_csv("y_test.csv")
    
    naive_bayes_classifier = load_model(model_name)

    x_test_vector = vectorizer.transform(full_x_test[1:800])
    x_test_vector = x_test_vector.toarray()
    y_pred = naive_bayes_classifier.predict(x_test_vector)

    probs = naive_bayes_classifier.predict_proba(x_test_vector)

    """
    with open("naiveBayesProbs.csv", 'a+', newline='') as csvfile:  
        # creating a csv writer object  
            csvwriter = csv.writer(csvfile) 
        
            for idx, i in enumerate(probs):
                    csvwriter.writerow(f"{y_pred[idx]} {probs[idx]}")
    """             

    
    
    print(accuracy_score(full_y_test[1:800], y_pred))
    conf_matrix = confusion_matrix(full_y_test[1:800], y_pred, labels=["0", "4"])
    print(conf_matrix)
    disp = plot_confusion_matrix(naive_bayes_classifier, x_test_vector, full_y_test[1:800], labels=["0","4"])
    print(disp)
    plt.show()

    # Need to investigate N-grams after
        

    #feature_nd = features.toarray()



    
#text_classifier()
#open_csv("x_train.csv")

def getMongo():
    client = MongoClient('mongodb://127.0.0.1:27017/')
    db = client["spotifyDatabase"]
    return db

def run_model(modelName):
    # Function that reads in tweets from the Mongo database, classifies their sentiment, and writes it back to the database.

    mongodb = getMongo()

    batchsize = 800
    current_position = 3038994
    totalTweetCount = mongodb.tweetsCollection2.count()
    print("Number of tweets in the database (to be classified): ", totalTweetCount)

    while current_position < totalTweetCount:
        currentDocumentBatch = mongodb.tweetsCollection2.find()[current_position:current_position+batchsize+1]
        currentDocumentBatch = [i for i in currentDocumentBatch]
        currentTweets = [i['text'] for i in currentDocumentBatch]
        currentIds = [i['_id'] for i in currentDocumentBatch]

        model = load_model(modelName)

        vectorizer = get_vectorizer()
        vectorized_tweets = vectorizer.transform(currentTweets)
        vectorized_tweets = vectorized_tweets.toarray()
        classifications = model.predict(vectorized_tweets)


        # Just need to sort out rewriting to the database.

        print("Latest Batch finished. Adding classifications for indexs: ", current_position, " through to: ", str(current_position+batchsize))
        for idx, i in enumerate(currentDocumentBatch):
            update_result = mongodb.tweetsCollection2.update_one(
                {"_id": currentIds[idx]},
                {"$set": { 
                    "sentiment": classifications[idx]
                }}
                , upsert=False)


            if update_result.raw_result["n"] == "0":
                # Tracking failed sentiment updates in a csv (will also conduct extra data quality at the end)
                with open("failedSentimentAdditions.csv", 'a+', newline='') as csvfile:  
                    csvwriter = csv.writer(csvfile) 
                    csvwriter.writerow(f"Failed ID: {currentIds[idx]}")
                    

        """
        currentDocumentBatch = mongodb.tweetsCollection2.find()[currentPosition:currentPosition+batchsize+1]
        currentDocumentBatch = [i for i in currentDocumentBatch]
        currentTweets = [i['text'] for i in currentDocumentBatch]
        currentIds = [i['_id'] for i in currentDocumentBatch]

        print("Current Documents (updated?): ")
        print(currentDocumentBatch)
        print("\n")
        """
        #end
        current_position += batchsize+1
        






"""
with open('twitterSentiment.csv', 'r', encoding="utf8") as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=','))
        for i in csv_reader[1:]:

            data.append(i[5])
            data_labels.append(i[0])
"""
#text_classifier()
#test_model("naiveBayes2.pkl")
run_model("naiveBayes2.pkl")