from flask import Flask, render_template
from dotenv import load_dotenv
import os
import requests
import json
import threading
import time

load_dotenv()

app = Flask(__name__)
DIALPAD_BEARER_TOKEN = os.getenv('DIALPAD_BEARER_TOKEN')
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

    print(f"\n=== Attempting to fetch data for {queue_type} ===")
    print(f"Call Center ID: {call_center_id}")
    print(f"Token available: {'Yes' if DIALPAD_BEARER_TOKEN else 'No'}")

    try:
        print("Making API request...")
        response = requests.get(url, headers=headers)
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")

        if response.status_code == 200:
            data = response.json()
            print(f"Raw response data: {data}")

            latest_data[queue_type]["longest_queue_time"] = int(data.get("longest_call_wait_time", 0)) // 60
            latest_data[queue_type]["agents_online"] = int(data.get("on_duty_operators", 0))
            latest_data[queue_type]["calls_in_queue"] = int(data.get("pending", 0))
            latest_data[queue_type]["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")

            print(f"Data updated for {queue_type}:")
            print(latest_data[queue_type])
        else:
            print(f"Error response: {response.text}")

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        print(f"Exception type: {type(e)}")

def call_api():
    """Main function to continuously fetch data from both call centers"""
    while True:
        get_call_center_data("4881687973216256", "billing")
        get_call_center_data("5237937156145152", "product")
        time.sleep(60)

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}, 200

@app.route('/')
def index():
    """Main route that displays the dashboard"""
    return render_template('index.html', data=latest_data)

def initialize_app():
    """Initialize the application and start the API polling thread"""
    api_thread = threading.Thread(target=call_api)
    api_thread.daemon = True
    api_thread.start()
