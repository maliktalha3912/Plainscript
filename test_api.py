import urllib.request
import json

data = json.dumps({"code": 'show "hello"', "inputs": []}).encode('utf-8')
req = urllib.request.Request('http://localhost:5000/run', data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))
