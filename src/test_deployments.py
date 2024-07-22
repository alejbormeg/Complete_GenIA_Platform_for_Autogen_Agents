import requests
import json

url = "http://localhost:8000/api/text_to_vectordb"

# Example payload
payload = {
    "text": "This is a sample text",
    "chunk_size": 1536,
    "embedding_model": "text-embedding-3-large"
}

response = requests.post(url, data=json.dumps(payload))

# Check the response status code
if response.status_code == 200:
    print("Test successful. Response:", response.json())
else:
    print("Test failed with status code:", response.status_code)