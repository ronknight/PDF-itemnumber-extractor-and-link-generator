from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import pdfplumber
import requests
from bs4 import BeautifulSoup
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
        # Extract item data (item numbers and titles)
        item_data = extract_item_data(file_path)
        logging.info(f"Extracted item data: {item_data}")

        # Generate links for each item
        items_with_links = []
        for item in item_data:
            title = item.get("title", "Product")  # Set default to "Product" if title is missing
            item_number = item.get("item_number")
            google_link = f"https://www.google.com/search?q=wholesale+{title.replace(' ', '+')}"
            fsgm_link = f"https://www.4sgm.com/lsearch.jhtm?cid=&keywords={item_number}"
            items_with_links.append({'item': item_number, 'title': title, 'google_link': google_link, 'fsgm_link': fsgm_link})

        return render_template('results.html', items=items_with_links)
    except Exception as e:
        logging.error(f"Error processing the PDF: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Deleted file {file_path}")

def fetch_product_title(item_number):
    """Scrapes product title from 4sgm.com based on item number."""
    search_url = f"https://www.4sgm.com/lsearch.jhtm?cid=&keywords={item_number}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(search_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find the image tag in the item image wrapper and extract the 'alt' text
            img_tag = soup.find("div", class_="item_image_wrapper").find("img")
            if img_tag and 'alt' in img_tag.attrs:
                return img_tag['alt']
    except Exception as e:
        logging.error(f"Error fetching title for {item_number}: {e}")
    
    return "Product"  # Default if title not found

def extract_item_data(pdf_path):
    """Extracts item numbers from PDF and fetches titles by scraping 4sgm.com."""
    item_data = []
    pattern_item = r'\b\d{5,6}[A-Z]?\b'  # Regex for item numbers

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                item_numbers = re.findall(pattern_item, text)

                for item_number in item_numbers:
                    title = fetch_product_title(item_number)
                    item_data.append({"item_number": item_number, "title": title})
    except Exception as e:
        logging.error(f"Error extracting item data from PDF: {e}")
        raise e

    return item_data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
