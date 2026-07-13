import pandas as pd
import string
import re
import ssl
import time
import os
import concurrent.futures
import matplotlib
matplotlib.use('Agg') # Set non-interactive backend
import matplotlib.pyplot as plt
from transformers import pipeline
import tempfile
from google.cloud import storage




def analyze_file(file_path='data/tmo_comments.xlsx'):
    print(f"Analyzing file: {file_path}")
    
    gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
    temp_local_path = None
    
    if gcs_bucket_name:
        try:
            print(f"Fetching file '{file_path}' from GCS bucket '{gcs_bucket_name}'...")
            storage_client = storage.Client()
            bucket = storage_client.bucket(gcs_bucket_name)
            blob = bucket.blob(file_path)
            
            temp_dir = tempfile.gettempdir()
            temp_local_path = os.path.join(temp_dir, os.path.basename(file_path))
            blob.download_to_filename(temp_local_path)
            read_path = temp_local_path
            print(f"Downloaded GCS file to temporary path: {read_path}")
        except Exception as e:
            print(f"Error fetching file from GCS: {e}")
            return None
    else:
        read_path = file_path
        if not os.path.exists(read_path):
            print(f"File not found: {read_path}")
            return None

    try:
        if read_path.endswith('.xlsx') or read_path.endswith('.xls'):
            data = pd.read_excel(read_path)
        elif read_path.endswith('.csv'):
            data = pd.read_csv(read_path)
        else:
            print("Unsupported file format.")
            return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    finally:
        if temp_local_path and os.path.exists(temp_local_path):
            try:
                os.remove(temp_local_path)
                print(f"Cleaned up temporary path: {temp_local_path}")
            except Exception as cleanup_err:
                print(f"Error cleaning up temp file {temp_local_path}: {cleanup_err}")


    # Extract comments, drop NaN values, convert to string, and flatten the list of lists
    raw_comments = data['Customer Feedback Filtered'].dropna().astype(str).tolist()
    customer_comments = [comment for sublist in raw_comments for comment in (sublist if isinstance(sublist, list) else [sublist])] if any(isinstance(x, list) for x in raw_comments) else raw_comments
    # Ensure all comments are strings
    customer_comments = [str(comment) for comment in customer_comments]

    # Remove any empty strings that might result from cleaning
    customer_comments = [comment for comment in customer_comments if comment.strip()]

    df = pd.DataFrame({
        'Comments': customer_comments
    })
    
    import torch
    device = 0 if torch.cuda.is_available() else -1
    sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=device)
    
    def categorize_sentiment(text):
        result = sentiment_pipeline(text)[0]
        label = result['label']
        score = result['score']

        if label == 'POSITIVE':
            if score >= 0.95:
                return 'STRONG_POSITIVE'
            elif score >= 0.7:
                return 'POSITIVE'
            else:
                # For positive sentiment with lower confidence, might be neutral or mixed
                return 'NEUTRAL' # Defaulting to POSITIVE for now
        elif label == 'NEGATIVE':
            if score >= 0.95:
                return 'STRONG_NEGATIVE'
            elif score >= 0.7:
                return 'NEGATIVE'
            else:
                # For negative sentiment with lower confidence
                return 'NEGATIVE' # Defaulting to NEGATIVE for now
        return 'NEUTRAL' # Fallback for unexpected labels or very low scores

    # Apply sentiment analysis to the customer comments
    print("Analyzing sentiment for customer comments...")
    sentiments = [categorize_sentiment(comment) for comment in customer_comments]

    # Add sentiments to the DataFrame
    df['Sentiment'] = sentiments
    print("\nSentiment analysis complete. Displaying first 10 comments with their sentiment:")
    print(df[['Comments', 'Sentiment']].head(10))
    print("\nSentiment distribution:")
    print(df['Sentiment'].value_counts())
    

    #New File Generation
    file_name = 'generated_files/sentiment_analysis.xlsx'
    df.to_excel(file_name, index=False)
    # Calculate the value counts for each identified topic
    sentiment_counts = df['Sentiment'].value_counts()

    # Create a bar chart
    plt.figure(figsize=(12, 8)) # Increased size
    sentiment_counts.plot(kind='bar', color='#3b82f6') # Added color
    plt.title('Distribution of Sentiments', fontsize=16)
    plt.xlabel('Sentiment', fontsize=12)
    plt.ylabel('Number of Comments', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save the plot
    chart_path = 'charts/sentiment_chart.png'
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
    
    analyze_file(default_path)