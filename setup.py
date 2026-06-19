from openai import OpenAI
import tweepy 
from credentials import bearer_token, api_key, api_key_secret, access_token, access_token_secret
from credentials import openai_api_key
from credentials import github_api_key


openai_client = OpenAI(api_key=openai_api_key)


x_client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_key_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )

PAIR = "0xd9eDC75a3a797Ec92Ca370F19051BAbebfb2edEe"