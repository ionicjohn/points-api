from flask import Flask, request
from flask_cors import CORS, cross_origin
from populate_point_tree import generate_points
from populate_file_tree import get_last_generation_date, get_last_cached_simplified_tree, populate_file_tree, get_last_cached_full_tree, check_configuration
from threading import Thread
import json
import os
import time

app = Flask("liczenie")
cors = CORS(app)

start_time = 0
error = None

def clear_cache_files():
    try:
        os.remove('output.json')
        os.remove('output_info.json')
        return True
    except Exception as e:
        return str(e)

@app.route('/api/cached')
def cached():
    date = get_last_generation_date()
    if not date:
        return json.dumps({"output": []}), 200
    return json.dumps({
        "time": date,
        "output": get_last_cached_simplified_tree()
    })
   
@app.route('/api/populateFileTree', methods=['POST'])
def generate():
    if start_time != 0:
        return json.dumps({"already_running": True}), 400
    def thread():
        print("[!] file generation started")

        global start_time, error
        start_time = int(time.time())
        error = None

        try:
            populate_file_tree()
        except Exception as e:
            error = str(e)

        start_time = 0

        print("[!] file generation completed")
    Thread(target=thread).run()
    return json.dumps({"status": "git"}), 200
@app.route('/api/populatePointsTree', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*')
def generate_point_s():
    if not get_last_generation_date():
        return {}, 400
    cached_tree = get_last_cached_full_tree()
    checkedNodes = request.get_json()['checkedNodes']
    organization = request.get_json()['organization']
    tree, output = generate_points(cached_tree, organization, checkedNodes)
    return json.dumps({
        "tree": tree,
        "output": output
    })

@app.route('/api/generate/status')
def get_status():
    global error
    if error != None:
        return json.dumps({"error": error})

    if start_time == 0:
        if get_last_generation_date():
            return json.dumps({"already_generated": True}), 200

        return json.dumps({"not_running": True}), 200

    return json.dumps({"elapsed": int(time.time()) - start_time}), 200


@app.route('/api/clearCache', methods=['DELETE'])
def clear_cache():
    result = clear_cache_files()
    if result == True:
        return json.dumps({"message": "Cache cleared successfully"}), 200
    else:
        return json.dumps({"error": result}), 500
if __name__ == "__main__":
    check_configuration()
    app.run(os.environ.get("host", "127.0.0.1"), int(os.environ.get("port", "9390")), debug=True)