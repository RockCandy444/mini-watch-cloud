"""Synthetic Ethernet/IPv4/UDP PCAP. No sniffing and no HTTP report input."""
import argparse
import ipaddress
import json
import struct
from pathlib import Path


def packet(payload_size):
    payload = b'x' * payload_size
    udp = struct.pack('!HHHH', 12345, 9999, 8 + len(payload), 0) + payload
    source, target = (ipaddress.ip_address(ip).packed for ip in ('192.0.2.10', '198.51.100.20'))
    header = struct.pack('!BBHHHBBH4s4s', 0x45, 0, 20 + len(udp), 1, 0, 64, 17, 0, source, target)
    total = sum(struct.unpack('!10H', header))
    while total >> 16:
        total = (total & 65535) + (total >> 16)
    checksum = (~total) & 65535
    header = header[:10] + struct.pack('!H', checksum) + header[12:]
    # Locally administered MACs; link type 1 is Ethernet.
    ethernet = bytes.fromhex('0200000000020200000000010800')
    return ethernet + header + udp


def generate(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as handle:
        handle.write(struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1))
        for index, offset_us in enumerate((0, 250000, 900000, 1000000, 2000000, 4999000, 5000000, 6000000)):
            frame = packet((index + 1) * 10)
            seconds, micros = divmod(offset_us, 1000000)
            handle.write(struct.pack('<IIII', 1700000000 + seconds, micros, len(frame), len(frame)))
            handle.write(frame)


def read_packets(path):
    with path.open('rb') as handle:
        header = handle.read(24)
        if len(header) != 24 or struct.unpack('<IHHIIII', header) != (0xa1b2c3d4, 2, 4, 0, 0, 65535, 1):
            raise ValueError('이 실습에서 생성한 little-endian microsecond Ethernet PCAP만 지원합니다.')
        rows = []
        while record := handle.read(16):
            if len(record) != 16:
                raise ValueError('불완전한 레코드 헤더입니다.')
            seconds, micros, captured, original = struct.unpack('<IIII', record)
            if micros >= 1000000 or captured > 65535 or captured > original:
                raise ValueError('패킷 헤더 범위가 올바르지 않습니다.')
            if len(handle.read(captured)) != captured:
                raise ValueError('불완전한 패킷입니다.')
            rows.append({'timestamp_us': seconds * 1000000 + micros, 'bytes': captured})
        return rows


def summarize(rows, window_seconds):
    start = min(row['timestamp_us'] for row in rows) if rows else 0
    selected = [row for row in rows if 0 <= row['timestamp_us'] - start < window_seconds * 1000000]
    return {'window_seconds': window_seconds, 'packet_count': len(selected),
            'byte_sum': sum(row['bytes'] for row in selected)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', type=Path, default=Path(__file__).with_name('data') / 'educational.pcap')
    args = parser.parse_args()
    generate(args.path)
    rows = read_packets(args.path)
    print(json.dumps({'source': 'educational_generated_not_live', 'total_packets': len(rows),
                      'comparisons': [summarize(rows, seconds) for seconds in (5, 1)]}, indent=2))
