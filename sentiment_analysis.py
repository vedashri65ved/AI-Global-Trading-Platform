from textblob import TextBlob

news = input("Enter News: ")

analysis = TextBlob(news)

polarity = analysis.sentiment.polarity

print("Polarity:", polarity)

if polarity > 0:

    print("Positive News")

elif polarity < 0:

    print("Negative News")

else:

    print("Neutral News")