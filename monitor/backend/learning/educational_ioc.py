"""Documentation-only IP string matching; never enrich real HTTP rows."""
import json

INDICATORS = {'192.0.2.10'}


def match_ioc(document_ip, indicators):
    return {'document_ip': document_ip, 'matched': document_ip in indicators,
            'source': 'documentation_example_not_live'}


if __name__ == '__main__':
    print(json.dumps([match_ioc(ip, INDICATORS) for ip in ('192.0.2.10', '198.51.100.20')], indent=2))
