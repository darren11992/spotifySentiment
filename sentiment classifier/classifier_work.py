import pandas as pd
from sklearn.model_selection import train_test_split
import spacy
import csv

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

def text_classifier():
    nlp = spacy.load("en_core_web_sm")
    textcat = nlp.create_pipe( "textcat", config = {"exclusive_classes": True, "architecture": "simple_cnn"})
    textcat.add_label("Positive")
    textcat.add_label("Negative")
    textcat.add_label("Neutral")

    nlp.add_pipe(textcat, last=True)

    print(nlp.pipe_names)
    x_train = open_csv("x_train.csv")
    y_train = open_csv("y_train.csv")

    

#text_classifier()
open_csv("x_train.csv")