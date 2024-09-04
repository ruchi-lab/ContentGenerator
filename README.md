# Content Idea Generator

## Overview
The **Content Idea Generator** is a Streamlit-based application that fetches posts from Reddit, analyzes their sentiment using the VADER sentiment analysis model, and generates content ideas based on trending topics. It uses MongoDB to store and manage data, and integrates with OpenAI's API to generate creative content ideas.

## Features
- Fetches top posts from a specified subreddit.
- Analyzes sentiment of posts and comments using the VADER sentiment analysis model.
- Stores posts and comments in MongoDB.
- Generates content ideas based on trending topics using OpenAI's API.

## Components
- **Streamlit**: Provides the user interface for interacting with the application.
- **PRAW (Python Reddit API Wrapper)**: Fetches data from Reddit.
- **VADER (Valence Aware Dictionary and sEntiment Reasoner)**: Analyzes the sentiment of text.
- **OpenAI's API**: Generates content ideas based on trending topics.
- **MongoDB**: Stores posts and comments.

## Installation

### Prerequisites
- Python 3.x
- MongoDB
- Access to OpenAI API

### Setting Up the Environment

1. **Clone the Repository**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Create a Virtual Environment**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up Environment Variables**

    Create a `.env` file in the root directory of the project with the following content:

    ```plaintext
    CLIENT_ID=<your_reddit_client_id>
    CLIENT_SECRET=<your_reddit_client_secret>
    MONGO_URI=<your_mongodb_uri>
    OPENAI_API_KEY=<your_openai_api_key>
    ```

## How It Works

1. **Fetching Data from Reddit**

    The `extract_posts` function uses the PRAW library to fetch top posts from a specified subreddit. It retrieves post details such as title, score, number of comments, and selftext. The fetched posts are then stored in the MongoDB posts collection.

    ```python
    def extract_posts(subreddit_name, limit=100):
        subreddit = reddit.subreddit(subreddit_name)
        posts = []
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
            posts_collection.update_one({'id': post.id}, {'$set': post_data}, upsert=True)
        return posts
    ```

2. **Analyzing Sentiment with VADER**

    The `analyze_and_update_sentiment` function uses VADER to analyze the sentiment of each post and comment. It assigns a sentiment score and label (positive, negative, or neutral) to each document.

    ```python
    def analyze_and_update_sentiment(collection):
        documents = collection.find()
        for document in documents:
            text = document['title'] if 'title' in document else document['body']
            sentiment_scores = sia.polarity_scores(text)
            collection.update_one(
                {'_id': document['_id']},
                {'$set': {
                    'sentiment': sentiment_scores['compound'],
                    'sentiment_label': 'positive' if sentiment_scores['compound'] > 0.05 else 'negative' if sentiment_scores['compound'] < -0.05 else 'neutral'
                }}
            )
    ```

3. **Generating Content Ideas with OpenAI's API**

    The `generate_content` function sends a prompt to OpenAI's API to generate content ideas based on trending topics. It uses the GPT-3.5-turbo model to create creative and engaging content.

    ```python
    def generate_content(prompt, max_tokens=2000):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        content = response.json()['choices'][0]['message']['content'].strip()
        return content
    ```

## Running the Application

1. **Start the MongoDB Server**

    Ensure MongoDB is running on your local machine or a remote server.

2. **Run the Streamlit App**

    ```bash
    streamlit run app.py
    ```

    Replace `app.py` with the filename of your Streamlit script.

3. **Interact with the Application**

    Open your web browser and navigate to `http://localhost:8501` to interact with the application. Enter a subreddit name to generate content ideas based on the latest posts.

## License

This project is licensed under the MIT License. See the [LICENSE](https://choosealicense.com/licenses/mit/) file for details.

## Acknowledgements
- [PRAW Documentation](https://praw.readthedocs.io/en/latest/)
- [NLTK Documentation](https://www.nltk.org/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)

