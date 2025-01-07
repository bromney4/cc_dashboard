from app import app, initialize_app
import os
import logging

logging.info("=== Starting application initialization ===")
logging.info(f"DIALPAD_BEARER_TOKEN present: {'Yes' if os.getenv('DIALPAD_BEARER_TOKEN') else 'No'}")
initialize_app()
logging.info("=== Application initialization complete ===")
