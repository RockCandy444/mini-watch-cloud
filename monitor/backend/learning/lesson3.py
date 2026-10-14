import json
from .support import read_observation
from .normalize import normalize_events
from .http_rules import select_views

if __name__ == '__main__':
    views = select_views(normalize_events(read_observation()))
    print(json.dumps({'count': len(views), 'view_ids': [row['id'] for row in views]}, ensure_ascii=False, indent=2))
