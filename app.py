from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_cors import CORS
import pdfplumber
import os
import re
import logging

app = Flask(__name__)
CORS(app)

# Ensure uploads directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Logging setup
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

@app.route('/')
def index():
    # Display the HTML upload form when visiting the root URL
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    logging.info("Received file upload request.")
    if 'pdf' not in request.files:
        logging.error("No PDF file found in the request.")
        return jsonify({'error': 'No PDF uploaded'}), 400

    file = request.files['pdf']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    logging.info(f"File saved to {file_path}")

    try:
        # Extract item numbers
        item_numbers = extract_item_numbers(file_path)
        logging.info(f"Extracted item numbers: {item_numbers}")

        # Generate links for each item number
        items_with_links = []
        for item in item_numbers:
            google_link = f"https://www.google.com/search?q=wholesale%20{item}"
            fsgm_link = f"https://www.4sgm.com/lsearch.jhtm?cid=&keywords={item}"
            items_with_links.append({'item': item, 'google_link': google_link, 'fsgm_link': fsgm_link})

        return render_template('results.html', items=items_with_links)
    except Exception as e:
        logging.error(f"Error processing the PDF: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Deleted file {file_path}")

def extract_item_numbers(pdf_path):
    """Extracts item numbers from the provided PDF file."""
    item_numbers = []
    pattern = r'\b\d{5,6}[A-Z]?\b'  # Regex pattern for item numbers

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                item_numbers.extend(re.findall(pattern, text))
    except Exception as e:
        logging.error(f"Error extracting item numbers from PDF: {e}")
        raise e

    return item_numbers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
