from flask import Flask, render_template
from dotenv import load_dotenv
import os
import requests
import json
import threading
import time
import sys

# Configure logging to stdout
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
DIALPAD_BEARER_TOKEN = os.getenv('DIALPAD_BEARER_TOKEN')
logger.info(f"Token loaded: {'Yes' if DIALPAD_BEARER_TOKEN else 'No'}")

latest_data = {
    "billing": {
        "name": "Billing Queue",
        "longest_queue_time": 0,
        "agents_online": 0,
        "calls_in_queue": 0,
        "last_updated": ""
    },
    "product": {
        "name": "Product Support",
        "longest_queue_time": 0,
        "agents_online": 0,
        "calls_in_queue": 0,
        "last_updated": ""
    }
}

def get_call_center_data(call_center_id, queue_type):
    """Fetch data from Dialpad API for a specific call center"""
    url = f"https://dialpad.com/api/v2/callcenters/{call_center_id}/status"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {DIALPAD_BEARER_TOKEN}"
    }

    logger.info(f"\n=== Attempting to fetch data for {queue_type} ===")
    logger.info(f"Call Center ID: {call_center_id}")
    logger.info(f"Token available: {'Yes' if DIALPAD_BEARER_TOKEN else 'No'}")
    logger.info(f"URL: {url}")
    logger.info(f"Headers: {headers}")

    try:
        logger.info("Making API request...")
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        logger.info(f"Response content: {response.text}")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Raw response data: {data}")

            latest_data[queue_type]["longest_queue_time"] = int(data.get("longest_call_wait_time", 0)) // 60
            latest_data[queue_type]["agents_online"] = int(data.get("on_duty_operators", 0))
            latest_data[queue_type]["calls_in_queue"] = int(data.get("pending", 0))
            latest_data[queue_type]["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")

            logger.info(f"Data updated for {queue_type}:")
            logger.info(latest_data[queue_type])
        else:
            logger.error(f"Error response: {response.text}")

    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        logger.error(f"Exception type: {type(e)}")

def call_api():
    """Main function to continuously fetch data from both call centers"""
    logger.info("Starting API polling thread")
    while True:
        try:
            get_call_center_data("4881687973216256", "billing")
            get_call_center_data("5237937156145152", "product")
            logger.info("Sleeping for 60 seconds...")
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error in call_api thread: {str(e)}")
            time.sleep(60)  # Still sleep on error to prevent rapid retries

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "data_status": latest_data}, 200

@app.route('/')
def index():
    """Main route that displays the dashboard"""
    logger.info(f"Rendering index with data: {latest_data}")
    return render_template('index.html', data=latest_data)

def initialize_app():
    """Initialize the application and start the API polling thread"""
    logger.info("Initializing application...")
    api_thread = threading.Thread(target=call_api)
    api_thread.daemon = True
    api_thread.start()
    logger.info("API polling thread started")
