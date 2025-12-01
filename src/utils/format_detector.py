def detect_compression_format(file_path: str) -> str | None:
    try:
        with open(file_path, 'rb') as f:
            magic = f.read(8)

            if magic.startswith(b'HUFFMAN'):
                return 'huffman'
            elif magic.startswith(b'LZ77\0\0'):
                return 'lz77'
            elif magic.startswith(b'COMBI'):
                return 'combined'
            elif magic.startswith(b'RLE\0'):
                return 'rle'
            else:
                return None

    except Exception as e:
        print(f"Ошибки определения формата: {e}")
        return None