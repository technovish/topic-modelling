import pandas as pd
from google import genai
from google.genai import types
import string
import nltk
from nltk.corpus import stopwords
import re
import ssl
import time
import os
import matplotlib
matplotlib.use('Agg') # Set non-interactive backend
import matplotlib.pyplot as plt


#SSL Required to get the nltk stopwords
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')

#Preprocess the comments
def preprocess_text(text):
    # Convert text to lowercase
    text = str(text).lower()

    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Remove numbers
    text = re.sub(r'\d+', '', text)

    # Remove common English stop words
    stop_words = set(stopwords.words('english'))
    words = text.split()
    words = [word for word in words if word not in stop_words]
    text = ' '.join(words)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

#Gemini API Key

api_key = os.environ.get("GEMINI_API_KEY") # Get API key from environment variable
client = genai.Client(api_key=api_key) if api_key else None

def identify_topic_gemini(comment):
    if not comment or comment.isspace():
        return "No Topic (Empty Comment)"

    if not client:
        return "Gemini Client Not Initialized"

    return True

print(identify_topic_gemini("Hello"))

print(client)