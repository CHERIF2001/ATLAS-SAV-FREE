import requests
import json

try:
    response = requests.get("http://localhost:8000/api/tweets?page=1&limit=5")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total Tweets: {data.get('total')}")
        print(f"Data Length: {len(data.get('data', []))}")
        if len(data.get('data', [])) > 0:
            print("Sample Tweet:")
            print(json.dumps(data['data'][0], indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
