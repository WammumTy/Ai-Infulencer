# AI Influencer Bot

This repository contains a small Reddit bot powered by [PRAW](https://praw.readthedocs.io/) and HuggingFace Transformers. The bot can create posts, reply to relevant threads, and upvote content on the `webdev` subreddit. A lightweight Flask app provides a dashboard and runs the bot periodically using `apscheduler`.

## Environment Variables
Set the following variables in a `.env` file or your shell before running the bot:

- `REDDIT_CLIENT_ID` – Reddit API client ID
- `REDDIT_CLIENT_SECRET` – Reddit API client secret
- `REDDIT_USERNAME` – Reddit account username
- `REDDIT_PASSWORD` – Reddit account password
- `REDDIT_USER_AGENT` – custom user agent string for the Reddit API

## Installation
Use Python 3.8+ and install the dependencies with pip:

```bash
pip install -r requirements.txt
```

## Usage
### Running the Flask dashboard
Start the dashboard, which also schedules the bot to run every hour:

```bash
python app.py
```

The app exposes a simple web page at `http://127.0.0.1:8080/` that shows recent log messages and allows you to trigger the bot manually.

### Running the bot directly
You can also run the bot without the web interface:

```bash
python bot.py
```

## Scripts and Features
- **app.py** – Flask server with a background scheduler. Shows the activity log and lets you run the bot on demand.
- **bot.py** – Core logic that uses GPT‑2 and Stable Diffusion to generate posts, comments, and images. Relevant posts and comments are identified with a zero‑shot classifier.
- **test.py** – Simple check to verify CUDA availability.

Generated images and text activity are logged to `activity_log.txt`.

