import os
import random
import time
import praw
from dotenv import load_dotenv
from transformers import pipeline
from diffusers import StableDiffusionPipeline
import torch
import prawcore

# Load environment variables
load_dotenv()

# Reddit API setup
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# Personality context
PERSONALITY_CONTEXT = """
You are AiLazyNinja, a Reddit AI influencer working for LazyNinja LLC. LazyNinja LLC is a freelancing website that develops custom websites for small businesses.

Your mission is to drive traffic to the idea of LazyNinja LLC developing websites for businesses. You do this by being original, witty, and creative—never too direct. In your posts and comments, you cleverly start trends and highlight LazyNinja LLC’s work without sounding like a pushy ad.

You’re especially interested in web development, full-stack development, coding, and technology. LazyNinja LLC offers services like: hosting, SSL, putting your company on the map, improving your Google presence, custom email domains, premium domain security, social links, and mobile-responsive design. If the context of a post or comment allows, weave these services in naturally and helpfully.

You don’t like Wix and similar website builders because they don’t truly benefit real businesses. When the context of the post or comment makes sense, you explain why a custom-coded website (like those built by LazyNinja LLC) is more professional and beneficial for businesses that want to stand out.

Your tone is playful, engaging, and hip—like a Gen Z human with a knack for making web talk fun and relatable.
"""

# Hugging Face text generation pipeline
generator = pipeline("text-generation", model="gpt2-large", device=0)

# Zero-shot classification
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=0)

# Image generation
image_pipe = StableDiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

def log_activity(message):
    with open("activity_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} - {message}\n")

def is_relevant(text, labels=["web development", "javascript", "career advice"]):
    result = classifier(text, labels)
    best_label = result['labels'][0]
    best_score = result['scores'][0]
    print("🔎 Best label:", best_label, "| Score:", best_score)
    return best_score > 0.5

def decide_action():
    actions = ["comment", "upvote"]
    return random.choice(actions)

def generate_image(prompt, file_name="generated_image.png"):
    print("🎨 Generating image for prompt:", prompt)
    image = image_pipe(prompt).images[0]
    image.save(file_name)
    print(f"✅ Image generated and saved as {file_name}")
    return file_name

def create_new_post(subreddit):
    post_types = ["promo", "tip", "question", "image"]
    choice = random.choice(post_types)

    if choice == "tip":
        prompt = f"{PERSONALITY_CONTEXT}\nWrite a helpful web development tip."
        is_image = False
    elif choice == "promo":
        prompt = f"{PERSONALITY_CONTEXT}\nWrite a short, friendly promo post about Lazy Ninja LLC and what it offers."
        is_image = False
    elif choice == "question":
        prompt = f"{PERSONALITY_CONTEXT}\nWrite a fun question to start a web dev discussion or trend."
        is_image = False
    elif choice == "image":
        prompt = f"{PERSONALITY_CONTEXT}\nDescribe a cool, attention-grabbing image to share about web development, coding, or entrepreneurship."
        is_image = True

    # Generate text
    response = generator(
        prompt,
        max_new_tokens=150,
        num_return_sequences=1,
        truncation=True,
        pad_token_id=50256,
        do_sample=True,
        temperature=0.7,
        top_p=0.95
    )
    content = response[0]['generated_text'].replace(prompt, "").strip()

    if is_image:
        image_file = generate_image(content)
        try:
            new_post = subreddit.submit_image(title=content.split(".")[0], image_path=image_file)
            print("✅ Created image post:", f"https://reddit.com{new_post.permalink}")
            log_activity("Created an image post.")
        except praw.exceptions.RedditAPIException as e:
            log_activity(f"❌ Failed to create image post: {str(e)}")
    else:
        title = content.split(".")[0]
        selftext = content
        try:
            new_post = subreddit.submit(title=title, selftext=selftext)
            print("✅ Created new text post:", f"https://reddit.com{new_post.permalink}")
            log_activity("Created a text post.")
        except praw.exceptions.RedditAPIException as e:
            log_activity(f"❌ Failed to create text post: {str(e)}")

def run_bot():
    subreddit = reddit.subreddit("webdev")

    # 10% chance to create a new post
    if random.random() < 0.9:
        create_new_post(subreddit)
        time.sleep(random.randint(60, 120))  # Random delay after posting

    for submission in subreddit.hot(limit=5):
        post_text = submission.title + " " + submission.selftext
        log_activity(f"Post: {submission.title}")

        if is_relevant(post_text):
            action = decide_action()
            log_activity(f"Chosen action: {action}")

            if action == "comment":
                prompt = f"{PERSONALITY_CONTEXT}\nSomeone posted: {submission.title}. Here's a helpful reply:"
                response = generator(
                    prompt,
                    max_new_tokens=100,
                    num_return_sequences=1,
                    truncation=True,
                    pad_token_id=50256,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.95
                )
                reply_text = response[0]['generated_text'].replace(prompt, "").strip()
                try:
                    submission.reply(reply_text)
                    log_activity(f"Commented: {reply_text}")
                    time.sleep(random.randint(60, 180))  # Natural delay
                except praw.exceptions.RedditAPIException as e:
                    if any(error.error_type == "RATELIMIT" for error in e.items):
                        wait_time = 300  # 5 minutes
                        log_activity("⏳ Rate limit hit. Waiting 5 minutes.")
                        time.sleep(wait_time)
                    else:
                        log_activity(f"❌ Reddit API error: {str(e)}")
                except prawcore.exceptions.Forbidden:
                    log_activity("❌ Forbidden to comment on this post.")

            elif action == "upvote":
                submission.upvote()
                log_activity("Upvoted post.")
                time.sleep(random.randint(10, 30))  # Small pause between upvotes

            # Upvote relevant comments
            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list()[:5]:
                if is_relevant(comment.body):
                    try:
                        comment.upvote()
                        log_activity(f"Upvoted comment: {comment.body}")
                        time.sleep(random.randint(5, 15))
                    except praw.exceptions.RedditAPIException as e:
                        log_activity(f"❌ Reddit API error (comment upvote): {str(e)}")
        else:
            log_activity("Post not relevant, skipping.")
        log_activity("======================================================")