import requests
import json
try:
    resp = requests.get('http://127.0.0.1:9997/v3/paths/list')
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
