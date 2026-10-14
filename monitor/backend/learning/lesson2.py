import json
from .support import read_observation
from .normalize import normalize_events

if __name__ == '__main__':
    original = read_observation()
    normalized = normalize_events(original)
    print(json.dumps({'original_count': len(original), 'normalized_count': len(normalized),
                      'records': normalized}, ensure_ascii=False, indent=2))
