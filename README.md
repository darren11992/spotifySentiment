# spotifySentiment

Repo that contains (almost all of) my Final Year Project for my Computer Science degree that I completed at Cardiff University. The aim of the project was to determine if there was a link between the commercial performance of a musical artist, and the general sentiment of tweets about them. (Spoiler alert: there isn't, but I did get a 71% mark on this so I wasn't super upset at the time)

Contains:
- Scrappers that collected tweets from Twitter about various artists, and chart information from https://charts.spotify.com
- API calls to Spotify to collect extra artist information (genre, release date, album type etc)
- Script that trained and used a classifier to determine if collected tweets were positive or negative and stored everything in a local mongoDB.
- Also some openAI work that I did early in the project to see if it could do the classification for me (I haven't heard much from those guys in the years since....)

All done pretty quick and dirty, but its fun to look at in the years since. I also threw together a website with some nice charts of all this data- i'll dig this out at some point!

