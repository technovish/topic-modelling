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

    try:
        # Construct a prompt for topic identification, asking for concise topics
        prompt2 = f"Provide a concise main topic (1-3 words) or category for the following customer feedback comment:\nComment: {comment}\n\nTopic:"
        prompt = f"System Role: You are an expert Customer Feedback Analyst. Your goal is to analyze user comments and accurately categorize them into only one of five specific categories based on the primary intent of the message.\nCategories & Definitions:\nProduct Quality: Issues or praise regarding the physical item, software features, durability, or performance.\nService Quality: Feedback regarding company policies, shipping speed, website usability, or overall brand experience.\nAgent: Specific mentions of interactions with customer support staff, chat agents, or sales representatives (e.g., helpfulness, politeness, or lack thereof).\nPrice: Comments regarding the cost, value for money, subscription fees, or discounts.\nOthers: Any comment that does not fit the above categories or is too vague to classify.\nTask: Analyse the following comment. Do not create a new category on your own.\nComment: {comment}\n\nCategory:"
        # Generate content using the Gemini model
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=[prompt],
            config = types.GenerateContentConfig(
              max_output_tokens=50,  # Increased token limit for more descriptive topics
              
          )
        )
        # Extract the text from the response, handling cases where it might be empty
        if response.candidates and response.candidates[0].content.parts:
            topic = response.candidates[0].content.parts[0].text.strip()
            if not topic: # If the topic is still empty after stripping, assign a default
                return "No Topic Identified (Gemini - Empty Response)"
            return topic
        else:
            return "No Topic Identified (Gemini)"

    except Exception as e:
        # Log the error and return a default value
        print(f"Error processing comment '{comment[:900]}...': {e}")
        return "Error Identifying Topic"

def analyze_file(file_path):
    print(f"Analyzing file: {file_path}")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    try:
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            data = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        else:
            print("Unsupported file format.")
            return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

    # Determine column to use (looking for 'Customer Feedback Filtered' or similar)
    target_col = 'Customer Feedback Filtered'
    if target_col not in data.columns:
        print(f"Column '{target_col}' not found. Using the first text column.")
        # Fallback logic could be added here, currently just printing warning
        # For this refactor, let's strictly check or fail, or maybe look for 'reviews' or similar
        # If not found, print available columns
        print(f"Available columns: {data.columns.tolist()}")
        # Temporary fallback: try to find a column with 'feedback' or 'comment' in name
        possible_cols = [c for c in data.columns if 'feedback' in c.lower() or 'comment' in c.lower()]
        if possible_cols:
            target_col = possible_cols[0]
            print(f"Using column: {target_col}")
        else:
             print("Could not identify a text column for analysis.")
             return None
    data = data[data[target_col] != 'Na']
    data = data[data[target_col] != 'N/a']
    comments = data[target_col].dropna().astype(str)
    
    # Optional: limit for testing
    #comments = comments[:500]

    print("Preprocessing function 'preprocess_text' defined.")
    comments = comments.apply(preprocess_text)
    print("Preprocessing applied to comments series.")

    if client:
        print("Gemini client is configured.")
    else:
        print("Gemini client not found.")

    # Apply the function to the 'comments' Series and store in a new column
    print("Starting topic identification. This may take a while...")
    
    if 'identified_topic' not in data.columns:
        data['identified_topic'] = None

    # Iterate and apply with a delay
    for i, comment in comments.items():
        data.at[i, 'identified_topic'] = identify_topic_gemini(comment)
        if (i + 1) % 10 == 0:  # Print progress every 10 comments (adjusted for faster feedback)
            print(f"Processed {i + 1} comments for topic identification.")
        time.sleep(0.1)  # Small delay to avoid hitting API rate limits

    print("Topic identification complete.")
    print("\nSample of comments with identified topics:")
    print(data[[target_col, 'identified_topic']].head())

    file_name = 'new_file.xlsx'
    data.to_excel(file_name, index=False)
    # Calculate the value counts for each identified topic
    topic_counts = data['identified_topic'].value_counts()

    # Create a bar chart
    plt.figure(figsize=(12, 8)) # Increased size
    topic_counts.plot(kind='bar', color='#3b82f6') # Added color
    plt.title('Distribution of Identified Topics', fontsize=16)
    plt.xlabel('Identified Topic', fontsize=12)
    plt.ylabel('Number of Comments', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save the plot
    chart_path = 'chart.png'
    if os.path.exists(chart_path):
        os.remove(chart_path)
    plt.savefig(chart_path)
    plt.close()
    print(f"Chart saved to {chart_path}")

    # Return the processed dataframe
    return data

if __name__ == "__main__":
    # Default behavior if run directly
    default_path = 'data/tmo_comments.xlsx'
    # Check absolute path mostly for local dev environment consistency
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, default_path)
    
    analyze_file(full_path)