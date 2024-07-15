import requests
import json

url = "http://localhost:8000/text2vectors"

# Example payload
payload = {
    "text": "This is a sample text",
    "chunk_size": 3,
    "embedding_model": "text-embedding-3-large"
}

response = requests.post(url, data=json.dumps(payload))

# Check the response status code
if response.status_code == 200:
    print("Test successful. Response:", response.json())
else:
    print("Test failed with status code:", response.status_code)


# File name: hello_client.py
# import requests

# response = requests.post(
#     "http://localhost:8000/", json={"language": "spanish", "name": "Dora"}
# )
# greeting = response.text
# print(greeting)