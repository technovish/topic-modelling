# Topic Modelling Application

This is a web application that allows users to upload customer feedback data (in Excel or CSV format) and automatically categorizes each comment into specific topics using Google's Gemini API. 

## Features
- **File Upload:** Upload `.xlsx`, `.xls`, or `.csv` files containing customer feedback.
- **Automated Topic Classification:** Uses the Gemini 2.5 Flash model to categorize feedback into one of five main categories:
  - Product Quality
  - Service Quality
  - Agent
  - Price
  - Others
- **Data Preprocessing:** Cleans and processes the text using `nltk` to remove stop words, punctuation, and numbers.
- **Analytics & Visualization:** Generates a bar chart (`chart.png`) showing the distribution of identified topics.
- **Data Export:** Outputs a new Excel file (`new_file.xlsx`) containing the original comments alongside their newly identified topics.

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **AI/ML:** Google GenAI SDK (`gemini-2.5-flash`), NLTK
- **Data Manipulation:** Pandas
- **Visualization:** Matplotlib

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Gemini API Key:**
   - The application relies on the Gemini API.
   - Create a file named `.env` in the root of your project directory based on `.env.example`.
   - Add your Gemini API key to the `.env` file like this:
     ```env
     GEMINI_API_KEY=your_actual_api_key_here
     ```
   - The application will automatically load this key when run.

## Usage

1. **Start the Flask server:**
   ```bash
   python server.py
   ```
   The server will run on `http://127.0.0.1:5001`.

2. **Access the application:**
   - Open your web browser and navigate to `http://127.0.0.1:5001`.
   - Use the web interface to upload your feedback data file.
   - Wait for the analysis to complete. Once finished, you will be able to view the results chart and download the processed dataset.

## Project Structure
- `server.py`: Main Flask application that handles routing and file uploads.
- `topic_analysis.py`: Core script handling text preprocessing, communication with the Gemini API, topic classification, and chart generation.
- `index.html`: The primary web interface for file uploads.
- `results.html`: Web page to display the results of the analysis.
- `script.js` & `style.css`: Frontend interactivity and styling.
- `requirements.txt`: List of required Python packages (`flask`, `pandas`, `google-genai`, `nltk`, `openpyxl`).

## Notes on Data Format
The application expects the uploaded Excel or CSV file to have a text column to analyze. Ideally, this column should be named `Customer Feedback Filtered`. If not found, the script tries to locate any column with "feedback" or "comment" in its header.
