from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class RLEPair:
    count: int
    value: int

    def __repr__(self):
        return f"({self.count}, {chr(self.value) if 32 <= self.value <= 126 else f'0x{self.value:02x}'})"


class RLECompressor:
    def __init__(self, max_run_length=255):
        self.max_run_length = max_run_length

    def compress(self, input_path: str, output_path: str):
        try:
            with open(input_path, 'rb') as f:
                original_data = f.read()

            original_size = len(original_data)
            if original_size == 0:
                self._write_empty_file(output_path)
                return

            print(f"RLE: Прочитано {original_size} байт из {input_path}")

            encoded_pairs = self._encode_rle(original_data)

            self._write_compressed_data(output_path, encoded_pairs, original_size)

            print(f"RLE: Сжатие завершено. Кол-во пар: {len(encoded_pairs)}")

        except Exception as e:
            print(f"RLE: Ошибка сжатия: {e}")
            raise

    def decompress(self, input_path: str, output_path: str):
        try:
            with open(input_path, 'rb') as f:
                magic = f.read(4)
                if magic != b"RLE\0":
                    raise ValueError("Не валидный RLE сжатый файл")

                max_run_length = int.from_bytes(f.read(1), 'big')
                original_size = int.from_bytes(f.read(4), 'big')

                if original_size == 0:
                    with open(output_path, 'wb') as out_f:
                        out_f.write(b"")
                    return

                pairs = []
                while True:
                    pair_data = f.read(2)  # Каждая пара - 2 байта
                    if not pair_data or len(pair_data) < 2:
                        break

                    count = pair_data[0]
                    value = pair_data[1]
                    pairs.append(RLEPair(count, value))

            decoded_data = self._decode_rle(pairs, original_size)

            with open(output_path, 'wb') as f:
                f.write(decoded_data)

            print(f"Распаковка завершена. Декодировано {len(decoded_data)} байтов")

        except Exception as e:
            print(f"Ошибка распаковки: {e}")
            raise

    def _encode_rle(self, data: bytes) -> List[RLEPair]:

        if not data:
            return []

        pairs = []
        i = 0
        data_len = len(data)

        while i < data_len:
            current_byte = data[i]
            run_length = 1

            while (i + run_length < data_len and
                   data[i + run_length] == current_byte and
                   run_length < self.max_run_length):
                run_length += 1

            pairs.append(RLEPair(run_length, current_byte))
            i += run_length

        return pairs

    def _decode_rle(self, pairs: List[RLEPair], original_size: int) -> bytes:
        decoded_data = bytearray()

        for pair in pairs:
            decoded_data.extend([pair.value] * pair.count)

        return bytes(decoded_data[:original_size])

    def _write_empty_file(self, output_path: str):
        with open(output_path, 'wb') as f:
            f.write(b"RLE\0")  # Магическое число + версия
            f.write((0).to_bytes(1, 'big'))  # max_run_length
            f.write((0).to_bytes(4, 'big'))  # original_size

    def _write_compressed_data(self, output_path: str, pairs: List[RLEPair], original_size: int):
        with open(output_path, 'wb') as f:
            f.write(b"RLE\0")  # Магическое число + версия
            f.write(self.max_run_length.to_bytes(1, 'big'))
            f.write(original_size.to_bytes(4, 'big'))

            for pair in pairs:
                f.write(pair.count.to_bytes(1, 'big'))
                f.write(pair.value.to_bytes(1, 'big'))

    def analyze_efficiency(self, data: bytes) -> dict:
        original_size = len(data)
        pairs = self._encode_rle(data)
        compressed_size = len(pairs) * 2

        run_lengths = [pair.count for pair in pairs]
        max_run = max(run_lengths) if run_lengths else 0
        min_run = min(run_lengths) if run_lengths else 0

        return {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': (1 - compressed_size / original_size) * 100,
            'num_pairs': len(pairs),
            'max_run_length': max_run,
            'min_run_length': min_run,
            'efficiency': "High" if compressed_size < original_size * 0.7 else
            "Medium" if compressed_size < original_size * 0.9 else
            "Low"
        }