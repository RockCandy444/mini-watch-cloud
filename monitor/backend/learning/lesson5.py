import json
from .support import read_observation
from .report import build_report

if __name__ == '__main__':
    print(json.dumps(build_report(read_observation()), ensure_ascii=False, indent=2))
