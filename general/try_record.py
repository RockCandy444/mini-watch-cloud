import json

event = {"method": "GET", "path": "/posts/1", "status_code": 200}
print(json.dumps(event, ensure_ascii=False))
