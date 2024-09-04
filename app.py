import streamlit as st
import praw
from pymongo import MongoClient
import datetime
import pandas as pd
import nltk
nltk.download('vader_lexicon')
import pymongo
from pymongo import MongoClient
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
# Initialize VADER
sia = SentimentIntensityAnalyzer()
import requests
from collections import Counter
import time
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

import os
from dotenv import load_dotenv
load_dotenv()

# Ensure you have the necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# Access the environment variables and Initialize Reddit API
reddit = praw.Reddit(
    client_id = os.getenv("CLIENT_ID"),
    client_secret = os.getenv("CLIENT_SECRET"),
    user_agent = 'myApp'
)

# Access and Connect to MongoDB and OpenAI API
client = MongoClient(os.getenv("MONGO_URI"))
api_key = os.getenv("OPENAI_API_KEY")

# Test connection
db = client.test_database
collection = db.test_collection

# Connect to MongoDB
db = client['myDatabase']
posts_collection = db['posts']
comments_collection = db['comments']

# Function to extract posts from subreddits
def extract_posts(subreddit_name, limit=100):
    subreddit = reddit.subreddit(subreddit_name)
    posts = []
    
    # Extract top posts
    for post in subreddit.top(limit=limit):
        post_data = {
            'id': post.id,
            'title': post.title,
            'score': post.score,
            'num_comments': post.num_comments,
            'url': post.url,
            'created_utc': datetime.datetime.fromtimestamp(post.created_utc),
            'author': post.author.name if post.author else "N/A",
            'selftext': post.selftext
        }
        posts.append(post_data)
        
        # Insert post into MongoDB
        posts_collection.update_one({'id': post.id}, {'$set': post_data}, upsert=True)

    return posts

# Function to extract comments for a specific post
def extract_comments(post_id):
    post = reddit.submission(id=post_id)
    post.comments.replace_more(limit=0)  # Flatten comment tree
    comments = []
    
    # Extract comments
    for comment in post.comments.list():
        comment_data = {
            'id': comment.id,
            'post_id': post_id,
            'author': comment.author.name if comment.author else "N/A",
            'body': comment.body,
            'score': comment.score,
            'created_utc': datetime.datetime.fromtimestamp(comment.created_utc)
        }
        comments.append(comment_data)

        # Insert comment into MongoDB
        comments_collection.update_one({'id': comment.id}, {'$set': comment_data}, upsert=True)
    
    return comments





# Explore posts data
def explore_posts():
    print("\nExploring posts data...")
    # Convert posts to DataFrame for exploration
    posts = list(posts_collection.find())
    posts_df = pd.DataFrame(posts)
    print("Posts DataFrame:")
    print(posts_df.head())  # Display the first few rows

    # Display basic statistics
    print("\nPosts Statistics:")
    print(posts_df.describe())

    # Display unique authors
    print("\nUnique Authors in Posts:")
    print(posts_df['author'].nunique())

# Explore comments data
def explore_comments():
    print("\nExploring comments data...")
    # Convert comments to DataFrame for exploration
    comments = list(comments_collection.find())
    comments_df = pd.DataFrame(comments)
    print("Comments DataFrame:")
    print(comments_df.head())  # Display the first few rows

    # Display basic statistics
    print("\nComments Statistics:")
    print(comments_df.describe())

    # Display unique authors
    print("\nUnique Authors in Comments:")
    print(comments_df['author'].nunique())








def analyze_and_update_sentiment(collection):
    # Fetch documents from the collection
    documents = collection.find()
    
    # Loop over each document and analyze sentiment
    for document in documents:
        text = document['title'] if 'title' in document else document['body']
        sentiment_scores = sia.polarity_scores(text)
        
        # Update the document with sentiment scores
        collection.update_one(
            {'_id': document['_id']},
            {'$set': {
                'sentiment': sentiment_scores['compound'],
                'sentiment_label': 'positive' if sentiment_scores['compound'] > 0.05 else 'negative' if sentiment_scores['compound'] < -0.05 else 'neutral'
            }}
        )

def generate_content(prompt, max_tokens=2000):
    headers = {
        "Authorization":f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",  # Confirm the model name is appropriate for the chat API
        "messages": [{"role": "user", "content": prompt}],  # Chat-based format
        "max_tokens": max_tokens
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    print(response.json())
    content = response.json()['choices'][0]['message']['content'].strip()  # Adjusted for chat response structure
    # content = response.json()
    return content


def extract_keywords(text):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text.lower())
    keywords = [word for word in words if word.isalpha() and word not in stop_words]
    return keywords

# Add a function to get trending topics based on keyword frequencies and their average sentiments
def get_trending_topics(collection, limit=100):
    cursor = collection.find().limit(limit)
    keyword_sentiment = {}

    for document in cursor:
        keywords = extract_keywords(document['title'] + ' ' + document.get('selftext', ''))
        for keyword in keywords:
            if keyword in keyword_sentiment:
                keyword_sentiment[keyword].append(document['sentiment'])
            else:
                keyword_sentiment[keyword] = [document['sentiment']]

    # Calculate average sentiment for each keyword
    trending_topics = {}
    for keyword, sentiments in keyword_sentiment.items():
        average_sentiment = sum(sentiments) / len(sentiments)
        trending_topics[keyword] = average_sentiment

    # Sort topics by the number of mentions and average sentiment
    sorted_topics = sorted(trending_topics.items(), key=lambda item: -len(keyword_sentiment[item[0]]) * abs(item[1]))
    return sorted_topics[:20]

def generate_content_ideas(trending_topics):
    prompt = f"Generate five ideas for creating trending content about these topics: {trending_topics} with reference links."
    # content_idea = generate_content(prompt)
    return generate_content(prompt)
                              

def main():
    st.title("Content Idea Generator")
    subreddits = st.text_input("Enter a topic:")

    if st.button("Generate Content Ideas"):
        with st.spinner('Fetching and analyzing data...'):
            print(f"Extracting posts from subreddit: {subreddits}")
            extract_posts(subreddits, limit=100)  # Adjust limit as needed
            explore_posts()
            analyze_and_update_sentiment(posts_collection)
            
            trending_topics = get_trending_topics(posts_collection)
            for topic, sentiment in trending_topics:
                print(f"Topic: {topic}, Average Sentiment: {sentiment}")

            trending_topics = ','.join([i[0] for i in trending_topics])

            start = time.time()
            content_ideas = generate_content_ideas(trending_topics)
            end = time.time()
            print(content_ideas)
            print("The time of execution of above program is :", (end-start), "s")

            client.drop_database('myDatabase')

            # Display the generated content ideas
            st.write("Generated Content Ideas:")
            st.write(content_ideas)

        
        st.success("Content ideas generated successfully!")

if __name__ == "__main__":
    main()