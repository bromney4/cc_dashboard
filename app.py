from flask import Flask, render_template
from dotenv import load_dotenv
import os
import requests
import json
import threading
import time
import redis
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
DIALPAD_BEARER_TOKEN = os.getenv('DIALPAD_BEARER_TOKEN')

# Initialize Redis
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(redis_url)

def get_call_center_data(call_center_id, queue_type):
    """Fetch data from Dialpad API for a specific call center"""
    url = f"https://dialpad.com/api/v2/callcenters/{call_center_id}/status"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {DIALPAD_BEARER_TOKEN}"
    }

    logger.info(f"\n=== Attempting to fetch data for {queue_type} ===")
    logger.info(f"Call Center ID: {call_center_id}")

    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Raw response data: {data}")

            queue_data = {
                "name": "Billing Queue" if queue_type == "billing" else "Product Support",
                "longest_queue_time": int(data.get("longest_call_wait_time", 0)) // 60,
                "agents_online": int(data.get("on_duty_operators", 0)),
                "calls_in_queue": int(data.get("pending", 0)),
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Store in Redis
            redis_client.set(f"queue_data_{queue_type}", json.dumps(queue_data))
            logger.info(f"Data updated for {queue_type}: {queue_data}")

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
            time.sleep(60)

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}, 200

@app.route('/')
def index():
    """Main route that displays the dashboard"""
    try:
        # Get data from Redis
        billing_data = json.loads(redis_client.get("queue_data_billing") or '{}')
        product_data = json.loads(redis_client.get("queue_data_product") or '{}')

        data = {
            "billing": billing_data or {
                "name": "Billing Queue",
                "longest_queue_time": 0,
                "agents_online": 0,
                "calls_in_queue": 0,
                "last_updated": ""
            },
            "product": product_data or {
                "name": "Product Support",
                "longest_queue_time": 0,
                "agents_online": 0,
                "calls_in_queue": 0,
                "last_updated": ""
            }
        }
        logger.info(f"Rendering index with data: {data}")
        return render_template('index.html', data=data)
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return render_template('index.html', data={})

def initialize_app():
    """Initialize the application and start the API polling thread"""
    logger.info("Initializing application...")
    api_thread = threading.Thread(target=call_api)
    api_thread.daemon = True
    api_thread.start()
    logger.info("API polling thread started")
