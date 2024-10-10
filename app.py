# API/app.py this is our flask app for the API

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests

app = Flask(__name__)
CORS_URL = os.getenv("CORS_URL")
CORS(app, resources={r"/*": {"origins": CORS_URL}}, supports_credentials=True)

GOLANG_BACKEND_URL = os.getenv("GOLANG_BACKEND_URL")

@app.route("/api/<resource>", methods=["GET", "POST", "DELETE"])
def handle_resource(resource):
    try:
        headers = {}
        if 'Authorization' in request.headers:
            headers['Authorization'] = request.headers['Authorization']
        
        app.logger.info(f"Received request for resource: {resource}")
        app.logger.info(f"Headers: {headers}")

        if request.method == "GET":
            app.logger.info(f"Sending GET request to: {GOLANG_BACKEND_URL}/{resource}")
            response = requests.get(f"{GOLANG_BACKEND_URL}/{resource}", headers=headers)
        elif request.method == "POST":
            app.logger.info(f"Sending POST request to: {GOLANG_BACKEND_URL}/{resource}/create")
            app.logger.info(f"Request data: {request.json}")
            response = requests.post(f"{GOLANG_BACKEND_URL}/{resource}/create", json=request.json, headers=headers)
        elif request.method == "DELETE":
            skill_id = request.args.get('id')
            app.logger.info(f"Sending DELETE request to: {GOLANG_BACKEND_URL}/{resource}/delete?id={skill_id}")
            response = requests.delete(f"{GOLANG_BACKEND_URL}/{resource}/delete?id={skill_id}", headers=headers)
        
        app.logger.info(f"Response status code: {response.status_code}")
        app.logger.info(f"Response content: {response.text}")
        
        response.raise_for_status()
        if response.status_code == 200:
            trigger_revalidation()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error communicating with Go backend: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        app.logger.error(f"Error decoding JSON from Go backend: {str(e)}")
        return jsonify({"error": "Invalid response from server"}), 500
    
@app.route("/api/login", methods=["POST"])
def login():
    response = requests.post(f"{GOLANG_BACKEND_URL}/login", json=request.json)
    return jsonify(response.json()), response.status_code

@app.route("/api/<resource>/<id>", methods=["GET", "PUT"])
def handle_resource_by_id(resource, id):
    app.logger.info(f"Received {request.method} request for resource: {resource} with id: {id}")
    try:
        headers = {}
        if 'Authorization' in request.headers:
            headers['Authorization'] = request.headers['Authorization']
        
        app.logger.info(f"Headers: {headers}")
        
        if request.method == "GET":
            response = requests.get(f"{GOLANG_BACKEND_URL}/{resource}/{id}", headers=headers)
        elif request.method == "PUT":
            response = requests.put(f"{GOLANG_BACKEND_URL}/{resource}/{id}", headers=headers, json=request.json)
        
        app.logger.info(f"Response status code: {response.status_code}")
        app.logger.info(f"Response content: {response.text}")
        
        response.raise_for_status()
        if response.status_code == 200:
            trigger_revalidation()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error communicating with Go backend: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        app.logger.error(f"Error decoding JSON from Go backend: {str(e)}")
        return jsonify({"error": "Invalid response from server"}), 500

def trigger_revalidation():
    revalidation_url = os.getenv("NEXT_REVALIDATION_URL")
    revalidation_secret = os.getenv("REVALIDATION_SECRET")

    # Add this check
    if not revalidation_url:
        app.logger.error("NEXT_REVALIDATION_URL is not set")
        return

    payload = {
        "secret": revalidation_secret
    }

    try:
        response = requests.post(revalidation_url, json=payload)
        response.raise_for_status()
        app.logger.info("Revalidation triggered successfully")
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error triggering revalidation: {str(e)}")

    #app.logger.info(f"NEXT_REVALIDATION_URL: {os.getenv('NEXT_REVALIDATION_URL')}")
    #app.logger.info(f"REVALIDATION_SECRET: {os.getenv('REVALIDATION_SECRET')}")

if __name__ == "__main__":
    load_dotenv()
    GOLANG_BACKEND_URL = os.getenv("GOLANG_BACKEND_URL")
    NEXT_REVALIDATION_URL = os.getenv("NEXT_REVALIDATION_URL")
    REVALIDATION_SECRET = os.getenv("REVALIDATION_SECRET")
    app.run(debug=True, port=5000)