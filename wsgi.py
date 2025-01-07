from app import app, initialize_app
import os

print("=== Starting application initialization ===")
print(f"DIALPAD_BEARER_TOKEN present: {'Yes' if os.getenv('DIALPAD_BEARER_TOKEN') else 'No'}")
initialize_app()
print("=== Application initialization complete ===")
