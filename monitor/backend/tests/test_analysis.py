"""Pure rule tests: time boundaries, consistent evidence, no live data needed."""
import unittest
import os
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from pathlib import Path
from monitor.backend.event_rules import make_event
from monitor.backend.learning.normalize import normalize_event, normalize_events
from monitor.backend.learning.http_rules import select_views, analyze_http, find_following_errors
from monitor.backend.learning.report import build_report
from monitor.backend.learning.educational_pcap import generate, read_packets, summarize
from monitor.backend.learning.educational_ioc import match_ioc, INDICATORS


class AnalysisRulesTests(unittest.TestCase):
    def row(self, index=1, seconds=0, **changes):
        return {'id': index, 'occurred_at': datetime(2026, 10, 14, tzinfo=timezone.utc) + timedelta(seconds=seconds),
                'method': 'GET', 'path': '/', 'status_code': 200, 'event_type': 'post_list', **changes}

    def case(self, count):
        return [self.row(i + 1, i) for i in range(count)] + [self.row(count + 1, count, path='/training-missing', status_code=404, event_type='request_error')]

    def test_classification_preserves_login(self):
        for method, path, status, expected in [('GET', '/', 200, 'post_list'), ('GET', '/training-missing', 404, 'request_error'),
                ('POST', '/auth/login', 401, 'login_failure'), ('POST', '/auth/login', 200, 'login_success')]:
            self.assertEqual(make_event({'method': method, 'path': path, 'status_code': status})['event_type'], expected)
        self.assertIsNone(make_event({'method': 'GET', 'path': '/', 'status_code': True}))

    def test_normalization_copies_and_preserves(self):
        original = self.row(17)
        before = dict(original)
        result = normalize_event(original)
        self.assertEqual(original, before)
        self.assertEqual((result['id'], result['source'], result['kind']), ('http-17', 'http_live', 'post_list'))
        for key in ('method', 'path', 'status_code'):
            self.assertEqual(result[key], original[key])
        self.assertEqual(datetime.fromisoformat(result['occurred_at']), original['occurred_at'])
        self.assertNotIn('ip', result)
        self.assertNotIn('user', result)

    def test_each_view_condition(self):
        originals = [self.row()] + [self.row(i + 2, **change) for i, change in enumerate(
            [{'method': 'POST'}, {'path': '/other'}, {'status_code': 404}, {'event_type': 'http_request'}])]
        selected = select_views(normalize_events(originals))
        self.assertEqual([row['id'] for row in selected], ['http-1'])

    def test_four_twelve_and_threshold_boundary(self):
        for count, threshold, matched in ((4, 10, False), (12, 10, True), (12, 20, False), (10, 10, True)):
            report = build_report(self.case(count), threshold)
            self.assertEqual(len(report['cards']), 1)
            card = report['cards'][0]
            self.assertEqual((card['observed'], card['matched'], len(card['records'])), (count, matched, count + 1))
            self.assertEqual(card['evidence'], [row['id'] for row in card['records']])
            self.assertEqual(len(card['view_ids']), count)

    def test_threshold_reuses_same_rows(self):
        source = self.case(12)
        first = build_report(source, 10, 7, '2026-10-14T00:00:30+00:00')
        second = build_report(source, 20, 7, first['reference_time'])
        self.assertEqual(first['cards'][0]['records'], second['cards'][0]['records'])
        self.assertEqual(first['cards'][0]['evidence'], second['cards'][0]['evidence'])
        self.assertNotEqual(first['cards'][0]['matched'], second['cards'][0]['matched'])

    def test_following_error_time_edges_and_unsorted_views(self):
        source = [self.row(1, 10), self.row(2, 0)]
        for i, seconds in enumerate((9, 10, 10.001, 40, 40.001), 3):
            source.append(self.row(i, seconds, status_code=404, event_type='request_error', path='/missing'))
        source.append(self.row(8, 11, status_code=500, event_type='request_error'))
        normalized = normalize_events(source)
        self.assertEqual([row['id'] for row in find_following_errors(normalized, select_views(normalized))], ['http-5', 'http-6'])

    def test_no_views_no_following_errors(self):
        result = analyze_http(normalize_events([self.row(status_code=404, event_type='request_error')]))
        self.assertEqual((result['count'], result['records'], result['following_error_ids']), (0, [], []))

    def test_invalid_threshold_and_time(self):
        for value in (0, -1, True, '10', 100001):
            with self.assertRaises(ValueError):
                analyze_http([], value)
        with self.assertRaises(ValueError):
            normalize_event(self.row(occurred_at='2026-10-14T00:00:00'))

    def test_separate_pcap_window_edges(self):
        with TemporaryDirectory(dir=Path(__file__).resolve().parents[3] if os.name == 'nt' else None) as folder:
            path = Path(folder) / 'educational.pcap'
            generate(path)
            rows = read_packets(path)
            self.assertEqual(len(rows), 8)
            self.assertEqual(summarize(rows, 5), {'window_seconds': 5, 'packet_count': 6, 'byte_sum': 462})
            self.assertEqual(summarize(rows, 1), {'window_seconds': 1, 'packet_count': 3, 'byte_sum': 186})

    def test_ioc_string_match_only(self):
        self.assertTrue(match_ioc('192.0.2.10', INDICATORS)['matched'])
        self.assertFalse(match_ioc('198.51.100.20', INDICATORS)['matched'])


if __name__ == '__main__':
    unittest.main()
