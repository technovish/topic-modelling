# Topic Sentiment Analysis Application

This is a web application that allows users to upload customer feedback data (in Excel or CSV format) and automatically analyzes each comment to categorize its sentiment using a pre-trained Hugging Face transformer model.

## Features
- **User Authentication & Registration:** Secure user sign-up and sign-in pages utilizing hashed passwords and session management.
- **File Upload:** Upload `.xlsx`, `.xls`, or `.csv` files containing customer feedback.
- **Automated Sentiment Analysis:** Uses the Hugging Face `distilbert-base-uncased-finetuned-sst-2-english` model to categorize feedback into one of five sentiment categories:
  - `STRONG_POSITIVE`
  - `POSITIVE`
  - `NEUTRAL`
  - `NEGATIVE`
  - `STRONG_NEGATIVE`
- **Google Cloud Storage (GCS) Integration:** Optional GCS integration to upload and fetch files directly from a bucket, with a local filesystem fallback for development.
- **Dynamic GCS File Processing:** Standalone execution of the analysis script dynamically checks GCS for the most recently uploaded file when a bucket is configured.
- **Analytics & Visualization:** Generates a bar chart (`charts/sentiment_chart.png`) showing the distribution of sentiments.
- **Data Export:** Outputs a new Excel file (`generated_files/sentiment_analysis.xlsx`) containing the original comments alongside their analyzed sentiments.

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL
- **AI/ML:** Hugging Face Transformers (`distilbert-base-uncased-sst-2`), PyTorch, NLTK
- **Cloud:** Google Cloud Storage (GCS) SDK, Google App Engine (GAE)
- **Security:** Werkzeug (for password hashing and verification)
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

4. **Set up Environment Variables:**
   - Create a file named `.env` in the root of your project directory based on `.env.example`.
   - Add your environment configuration details to the `.env` file like this:
     ```env
     GEMINI_API_KEY=your_actual_api_key_here
     
     # Database Configuration
     DB_HOST=localhost
     DB_USER=root
     DB_PASSWORD=your_password
     DB_NAME=comments
     DB_PORT=3306
     
     # Optional: Unix socket connection path (uncomment to override host/port TCP connection)
     # DB_SOCKET=/cloudsql/project-id:region:instance-id
     
     # Optional: Google Cloud Storage bucket name for file storage
     GCS_BUCKET_NAME=your-gcs-bucket-name
     ```

5. **Initialize Database:**
   - Run the database setup script to create the user tables and seed a default user:
     ```bash
     python setup_db.py
     ```
     *Note: This generates a default user with Email: `user@intellize.com`, Password: `intellize`.*

## Usage

1. **Start the Flask server:**
   ```bash
   python server.py
   ```
   The server will run on `http://127.0.0.1:5001`.

2. **Access the application:**
   - Open your web browser and navigate to `http://127.0.0.1:5001`.
   - You will be redirected to the sign-in page. Log in with the default credentials or click "Sign Up" to register a new account.
   - Use the main portal interface to upload your feedback data file.
   - Wait for the analysis to complete. Once finished, you will be able to view the results chart and download the processed dataset.

3. **Running Standalone Analysis:**
   - You can also run the analysis script directly via terminal:
     ```bash
     python topic_analysis.py [optional_local_file_path]
     ```
     If `GCS_BUCKET_NAME` is configured, it will check the bucket for the most recently uploaded file and analyze it.

4. **Running Tests:**
   - Run the unit tests to verify the authentication and file upload logic:
     ```bash
     python -m unittest test_login.py
     python -m unittest test_upload.py
     ```

## Running with Docker

Alternatively, you can build and run the application inside a Docker container:

1. **Build the Docker image:**
   ```bash
   docker build -t topic-modelling .
   ```

2. **Run the container:**
   ```bash
   docker run -p 5001:5001 --env-file .env topic-modelling
   ```

## Deploying to Google App Engine (GAE)

To deploy the application to Google App Engine Standard (Python 3.9 runtime):

1. Ensure you have the [Google Cloud CLI (gcloud)](https://cloud.google.com/sdk/gcloud) installed and configured.
2. Edit the [app.yaml](file:///Users/technovish/Personal/Repos/topic-modelling/app.yaml) file to fill in your environment variables, including `GEMINI_API_KEY`, database credentials (`DB_SOCKET`), and GCS bucket details under the `env_variables` section.
3. Deploy the application:
   ```bash
   gcloud app deploy
   ```

## Project Structure
- `server.py`: Main Flask application that handles authentication routes, session management, and file uploads.
- `setup_db.py`: Database initialization script creating the `users` table and creating the default seed user.
- `topic_analysis.py`: Core script handling text preprocessing, downloading files from GCS, analyzing sentiment using Hugging Face pipeline, and chart generation.
- `index.html`: The primary web interface for file uploads (requires active session).
- `login.html`: Secure Sign In interface.
- `register.html`: Secure Create Account interface.
- `invalid.html`: Validation failure page for invalid login.
- `results.html`: Web page to display the results of the analysis.
- `script.js` & `style.css`: Frontend interactivity, styling, and visual transitions.
- `test_login.py` & `test_upload.py`: Test suites checking authorization logic, login/signup API endpoint behaviors, and upload flows.
- `app.yaml`: Google App Engine deployment configuration.
- `requirements.txt`: List of required Python packages.

## Notes on Data Format
The application expects the uploaded Excel or CSV file to have a text column to analyze. Ideally, this column should be named `Customer Feedback Filtered`. If not found, the script tries to locate any column with "feedback" or "comment" in its header.
