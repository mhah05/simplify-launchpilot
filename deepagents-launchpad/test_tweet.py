import tweepy, os
from dotenv import load_dotenv
load_dotenv()

print("API_KEY:", os.getenv("X_API_KEY")[:6] + "..." if os.getenv("X_API_KEY") else "MISSING")
print("API_SECRET:", "present" if os.getenv("X_API_SECRET") else "MISSING")
print("ACCESS_TOKEN:", os.getenv("X_ACCESS_TOKEN")[:6] + "..." if os.getenv("X_ACCESS_TOKEN") else "MISSING")
print("ACCESS_TOKEN_SECRET:", "present" if os.getenv("X_ACCESS_TOKEN_SECRET") else "MISSING")

client = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
)

try:
    me = client.get_me()
    print("get_me() SUCCESS:", me.data)
except Exception as e:
    print("get_me() FAILED:", e)