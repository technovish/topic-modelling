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

api_key = 'AIzaSyBvboVCu8QEV8lmfIUz6TrMU6YILeVtarg'
client = genai.Client(api_key=api_key) if api_key else None

def identify_topic_gemini(comment):
    if not comment or comment.isspace():
        return "No Topic (Empty Comment)"

    if not client:
        return "Gemini Client Not Initialized"

    try:
        # Construct a prompt for topic identification, asking for concise topics
        prompt = f"Provide a concise main topic (1-3 words) or category for the following customer feedback comment:\nComment: {comment}\n\nTopic:"

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
        print(f"Error processing comment '{comment[:50]}...': {e}")
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

    comments = data[target_col].dropna().astype(str)
    
    # Optional: limit for testing
    comments = comments[:100] 

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