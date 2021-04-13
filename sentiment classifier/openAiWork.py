import openai
import csv
import random
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib
import matplotlib.pyplot as plt 

openai.organisation = "org-unNa1DPUJjTlfjH46MOAgkwa"
openai.api_key = "sk-AvuZwcK00mnZY2i0k9mDAF7i7DDjieOjTBJpg7vv"

def open_csv(csv_file):
    with open(csv_file, 'r', encoding="utf8") as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=','))
        fileList = [x[0] for x in csv_reader]
    return fileList

def open_ai_test():

    full_x_test = open_csv("x_test.csv")[1:]
    full_y_test = open_csv("y_test.csv")[1:]

    chunk_size = 10 
    current_position = 0

    with open("openAiResult.csv", 'w') as csvfile:  
        # creating a csv writer object  
        csvwriter = csv.writer(csvfile) 

    for i in range(10):

        current_position = random.randint(0, len(full_x_test))
        print("Starting postion chosen: ",  current_position)
        small_test_x = full_x_test[current_position:current_position+ chunk_size]
        small_test_y = full_y_test[current_position:current_position+ chunk_size]




        response = openai.Completion.create(
        engine="davinci",
        prompt=f"This is a tweet sentiment classifier\nTweet: \"I loved the new Batman movie!\"\nSentiment: Positive\n###\nTweet: \"I hate it when my phone battery dies\"\nSentiment: Negative\n###\nTweet: \"My day has been 👍\"\nSentiment: Positive\n###\nTweet: \"This is the link to the article\"\nSentiment: Neutral\n###\nTweet text\n\n\n1. \"I loved the new Batman movie!\"\n2. \"I hate it when my phone battery dies\"\n3. \"My day has been 👍\"\n4. \"This is the link to the article\"\n5. \"This new music video blew my mind\"\n\n\nTweet sentiment ratings:\n1: Positive\n2: Negative\n3: Positive\n4: Neutral\n5: Positive\n\n\n###\nTweet text\n\n\n1. \"{small_test_x[0]}\"\n2. \"{small_test_x[1]}\"\n3. \"{small_test_x[2]}\"\n4. \"{small_test_x[3]}\"\n5. \"{small_test_x[4]}\"\n6. \"{small_test_x[5]}\"\n7. \"{small_test_x[6]}\"\n8. \"{small_test_x[7]}\"\n9. \"{small_test_x[8]}\"\n10. \"{small_test_x[9]}\"\n\n\nTweet sentiment ratings:\n1.",
        temperature=0.3,
        max_tokens=60,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["###"]
        )


        print("full response:")
        print(response)
        print("\n")
        print("type:")
        print(type(response))
        print("\n")
        print("Text?:")
        print(response.choices[0]["text"])

        determined_sentiment = response.choices[0]["text"]
        determined_sentiment = determined_sentiment.split("\n")

        print("Split up results:")

        print(determined_sentiment)

        
        with open("openAiResult.csv", 'a+', newline='') as csvfile:  
        # creating a csv writer object  
            csvwriter = csv.writer(csvfile) 
        
            for idx, i in enumerate(determined_sentiment):
                if "Positive" in i:
                    csvwriter.writerow(f"4 {small_test_y[idx]}")
                elif "Neutral" in i or "Negative" in i:
                    csvwriter.writerow(f"0 {small_test_y[idx]}")
                    
            current_position += chunk_size


def plot_aiConfusion_matrix():
    open_ai_results = []
    actual_results = []
     
    with open('openAiResult.csv', 'r', encoding="utf8") as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=','))
        for i in csv_reader:
            open_ai_results.append(i[0].strip())
            actual_results.append(i[1].strip())


    print("HI!")
    print(actual_results)
    print(open_ai_results)
    cm = confusion_matrix(actual_results, open_ai_results, labels = ['0','4'])
    print(cm)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['0', '4'])
    disp.plot(include_values=True, cmap="viridis", xticks_rotation='horizontal', values_format=None, ax=None, colorbar=True) 
    plt.show()

plot_aiConfusion_matrix()
