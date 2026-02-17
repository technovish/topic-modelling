import argparse
import pandas as pd
import os
import sys
# Add current directory to path to allow import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from topic_analysis import identify_topic_gemini, preprocess_text
except ImportError:
    print("Error: Could not import topic_analysis. Make sure topic_analysis.py is in the same directory.")
    sys.exit(1)

def generate_golden_set(input_file, output_file, sample_size=20):
    """
    Generates a sample dataset for manual labeling.
    """
    print(f"Reading from {input_file}...")
    try:
        if input_file.endswith('.xlsx'):
            df = pd.read_excel(input_file)
        elif input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        else:
            print("Unsupported input format. Please use .xlsx or .csv")
            return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Find text column
    target_col = 'Customer Feedback Filtered'
    if target_col not in df.columns:
         # Fallback search
        possible_cols = [c for c in df.columns if 'feedback' in c.lower() or 'comment' in c.lower()]
        if possible_cols:
            target_col = possible_cols[0]
        else:
            print("Could not find a feedback/comment column.")
            return

    print(f"Sampling {sample_size} comments from '{target_col}'...")
    
    # Drop empty and sample
    df_clean = df[target_col].dropna().astype(str)
    if len(df_clean) > sample_size:
        sample = df_clean.sample(n=sample_size, random_state=42)
    else:
        sample = df_clean
    
    # Create evaluation dataframe
    eval_data = []
    
    print("Generating initial predictions...")
    for idx, comment in sample.items():
        # Replicate the pipeline: Preprocess -> Predict
        clean_comment = preprocess_text(comment)
        predicted = identify_topic_gemini(clean_comment)
        
        eval_data.append({
            'Original_Comment': comment,
            'Preprocessed_Comment': clean_comment,
            'Model_Predicted_Topic': predicted,
            'Manual_Actual_Topic': '' # User to fill this
        })
        print(".", end="", flush=True)
    print("\n")

    eval_df = pd.DataFrame(eval_data)
    
    # Save
    if not output_file:
        output_file = 'data/accuracy_evaluation_set.xlsx' # Default
        
    # Ensure dir exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if output_file.endswith('.csv'):
        eval_df.to_csv(output_file, index=False)
    else:
        eval_df.to_excel(output_file, index=False)
        
    print(f"Evaluation set generated at: {output_file}")
    print("ACTION REQUIRED: Open this file, fill in the 'Manual_Actual_Topic' column with the correct topics, and save it.")

def evaluate_accuracy(labeled_file):
    """
    Calculates accuracy metrics comparing Model vs Manual.
    """
    print(f"Reading labeled data from {labeled_file}...")
    try:
        if labeled_file.endswith('.xlsx'):
            df = pd.read_excel(labeled_file)
        elif labeled_file.endswith('.csv'):
            df = pd.read_csv(labeled_file)
        else:
             print("Unsupported file format.")
             return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    required_cols = ['Model_Predicted_Topic', 'Manual_Actual_Topic']
    if not all(col in df.columns for col in required_cols):
        print(f"Error: File must contain columns: {required_cols}")
        print(f"Found: {df.columns.tolist()}")
        return

    # Filter out empty manual labels (in case user missed some)
    df_scored = df.dropna(subset=['Manual_Actual_Topic'])
    if len(df_scored) == 0:
        print("No labeled data found. Please fill 'Manual_Actual_Topic' column.")
        return

    total = len(df_scored)
    exact_matches = 0
    partial_matches = 0
    
    print(f"Evaluating {total} labeled samples...\n")
    print(f"{'PREDICTED':<30} | {'ACTUAL':<30} | {'RESULT'}")
    print("-" * 80)

    for i, row in df_scored.iterrows():
        pred = str(row['Model_Predicted_Topic']).strip().lower()
        actual = str(row['Manual_Actual_Topic']).strip().lower()
        
        # Metric 1: Exact Match (Case insensitive)
        is_exact = pred == actual
        
        # Metric 2: Partial/Soft Match (Token overlap)
        pred_tokens = set(pred.split())
        actual_tokens = set(actual.split())
        # Jaccard like check: if any significant word overlaps? 
        # Or subset check. "Billing" == "Billing Issue" -> Partial
        overlap = pred_tokens.intersection(actual_tokens)
        is_partial = len(overlap) > 0
        
        if is_exact:
            exact_matches += 1
            result = "EXACT MATCH"
        elif is_partial:
            partial_matches += 1
            result = "PARTIAL MATCH"
        else:
            result = "MISSING"

        print(f"{pred[:28]:<30} | {actual[:28]:<30} | {result}")

    accuracy = (exact_matches / total) * 100
    soft_accuracy = ((exact_matches + partial_matches) / total) * 100

    print("-" * 80)
    print("\nRESULTS:")
    print(f"Total Samples: {total}")
    print(f"Exact Match Accuracy: {accuracy:.1f}%  (Strict string equality)")
    print(f"Soft Match Accuracy:  {soft_accuracy:.1f}%  (At least one word overlap)")
    print("\nNote: 'Soft Match' credits cases like 'Billing' matching 'Billing Issue'.")

def main():
    parser = argparse.ArgumentParser(description="Tool to measure Topic Modeling Accuracy")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate a sample Evaluation Set')
    gen_parser.add_argument('--input', default='data/tmo_comments.xlsx', help='Path to source data')
    gen_parser.add_argument('--output', default='data/evaluation_set.xlsx', help='Path to save evaluation set')
    gen_parser.add_argument('--n', type=int, default=20, help='Number of samples')

    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate accuracy from labeled file')
    eval_parser.add_argument('--file', required=True, help='Path to the filled evaluation set')

    args = parser.parse_args()

    if args.command == 'generate':
        generate_golden_set(args.input, args.output, args.n)
    elif args.command == 'evaluate':
        evaluate_accuracy(args.file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
