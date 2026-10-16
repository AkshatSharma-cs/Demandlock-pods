"""Generate placeholder PWA icons using only the Python standard library."""
from pathlib import Path
import struct
import zlib


def png(size: int) -> bytes:
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            center = size // 4 <= x < size * 3 // 4 and size // 4 <= y < size * 3 // 4
            row.extend((60, 103, 160, 255) if center else (20, 40, 75, 255))
        rows.append(bytes(row))

    def chunk(kind: bytes, data: bytes) -> bytes:
        checksum = struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + kind + data + checksum

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b"")


for dimension in (192, 512):
    target = Path("frontend/public/icons") / f"icon-{dimension}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(png(dimension))
