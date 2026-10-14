import json
from .support import read_observation
from .normalize import normalize_events
from .http_rules import analyze_http

if __name__ == '__main__':
    rows = normalize_events(read_observation())
    print(json.dumps([analyze_http(rows, threshold) for threshold in (10, 20)], ensure_ascii=False, indent=2))
