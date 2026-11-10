"""Decode the locally extracted Dreams Imp animation bank (version 1600)."""

import argparse
import json
import math
import struct
from pathlib import Path


class Reader:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def read(self, size):
        end = self.offset + size
        if size < 0 or end > len(self.data):
            raise ValueError(f'Truncated animation data at {self.offset:#x}')
        chunk = self.data[self.offset:end]
        self.offset = end
        return chunk

    def unpack(self, fmt):
        return struct.unpack(fmt, self.read(struct.calcsize(fmt)))


def parse_bank(data):
    # The layout and conditional count come from the game loader at 0x75b5a30.
    reader = Reader(data)
    version, count = reader.unpack('<II')
    if version != 1600:
        raise ValueError(f'Unsupported Imp animation bank version {version}')
    clips = []
    for _ in range(count):
        start = reader.offset
        name = reader.read(reader.unpack('<B')[0]).decode('ascii')
        header = reader.unpack('<BBHHHB')
        track_count, = reader.unpack('<I')
        if track_count and reader.unpack('<I')[0] != track_count:
            raise ValueError(f'Conflicting track counts in {name!r}')
        descriptors = list(struct.iter_unpack('<4H', reader.read(track_count * 8)))
        word_count, = reader.unpack('<I')
        words = reader.unpack(f'<{word_count}I')
        clips.append(dict(name=name, offset=start, header=header,
                          descriptors=descriptors, words=words))
    if reader.offset != len(data):
        raise ValueError(f'Unexpected data after the last clip at {reader.offset:#x}')
    return clips


def encode_bank(clips):
    chunks = [struct.pack('<II', 1600, len(clips))]
    for clip in clips:
        name = clip['name'].encode('ascii')
        chunks.extend((struct.pack('<B', len(name)), name,
                       struct.pack('<BBHHHB', *clip['header'])))
        tracks = clip['descriptors']
        chunks.append(struct.pack('<I', len(tracks)))
        if tracks:
            chunks.append(struct.pack('<I', len(tracks)))
            chunks.extend(struct.pack('<4H', *track) for track in tracks)
        words = clip['words']
        chunks.append(struct.pack(f'<I{len(words)}I', len(words), *words))
    return b''.join(chunks)


def decode_keys(clip, index):
    """Preserve raw payloads and split them at the game's key boundaries."""
    descriptor, first, last, offset = clip['descriptors'][index]
    channel = descriptor & 0xff
    words = clip['words']
    bounds = [d[3] for d in clip['descriptors'] if d[3] > offset]
    end = min(bounds, default=len(words))
    keys = []
    while offset < end:
        header = words[offset]
        frame = header & 0x1ff  # Frame mask from 0x75b56f0.
        # Key sizes follow the validator at 0x75b5660. Two channels carry
        # variable length payloads; the count for channel 0 is in vec4s.
        if header & 0x600:
            size = 0
        elif channel == 0 and offset + 4 < end:
            size = 4 + 4 * (words[offset + 4] & 0xffff)
        elif channel == 38 and offset + 1 < end:
            count, = struct.unpack('<f', struct.pack('<I', words[offset + 1]))
            if not math.isfinite(count) or count < 0 or not count.is_integer():
                raise ValueError(f'Invalid variable key count in {clip["name"]!r}')
            size = 1 + int(count)
        elif channel == 40:
            size = 2
        elif channel in (8, 9, 10, 21, 27, 36, 37, 39):
            size = 4
        elif channel in (1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14, 15, 16,
                         17, 18, 19, 20, 23, 25, 26, 29, 30, 31, 32, 33, 34, 41):
            size = 1
        else:
            raise ValueError(f'Unsupported or truncated channel {channel} in {clip["name"]!r}')
        if offset + 1 + size > end or (keys and frame < keys[-1]['frame']):
            raise ValueError(f'Invalid key bounds in {clip["name"]!r}')
        keys.append(dict(frame=frame, header=header,
                         payload=words[offset+1:offset+1+size]))
        offset += 1 + size
    if not keys or (keys[0]['frame'], keys[-1]['frame']) != (first, last):
        raise ValueError(f'Invalid key frame range in {clip["name"]!r}')
    return keys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bank', type=Path)
    parser.add_argument('--inventory', type=Path)
    args = parser.parse_args()
    data = args.bank.read_bytes()
    clips = parse_bank(data)
    if encode_bank(clips) != data:
        raise ValueError('Animation bank did not round trip byte for byte')
    track_count = key_count = 0
    for clip in clips:
        for i in range(len(clip['descriptors'])):
            key_count += len(decode_keys(clip, i))
            track_count += 1
    if args.inventory:
        inventory = [{**{k: v for k, v in c.items() if k != 'words'},
                      'word_count': len(c['words'])} for c in clips]
        args.inventory.write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
    print(f'Round-tripped {len(clips)} clips and {len(data):,} bytes exactly. '
          f'Decoded {track_count:,} tracks and {key_count:,} packed keys.')


if __name__ == '__main__':
    main()
