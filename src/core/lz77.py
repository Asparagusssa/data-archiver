from typing import Tuple
from src.models.lz77_models import LZ77Token, SlidingWindow


class LZ77Compressor:
    def __init__(self, window_size=4096, lookahead_size=18):
        self.window_size = window_size
        self.lookahead_size = lookahead_size

    def find_longest_match(self, search_buffer: bytes, lookahead_buffer: bytes) -> Tuple[int, int]:

        search_len = len(search_buffer)
        lookahead_len = len(lookahead_buffer)

        if lookahead_len == 0:
            return 0, 0

        best_offset = 0
        best_length = 0

        for offset in range(1, min(search_len, self.window_size) + 1):
            search_start = search_len - offset
            current_length = 0

            while (current_length < lookahead_len and
                   current_length < offset and
                   search_start + current_length < search_len and
                   search_buffer[search_start + current_length] == lookahead_buffer[current_length]):
                current_length += 1

            if current_length > best_length:
                best_length = current_length
                best_offset = offset

        return best_offset, best_length

    def compress(self, input_path: str, output_path: str):
        try:
            with open(input_path, 'rb') as f:
                original_data = f.read()

            original_size = len(original_data)
            if original_size == 0:
                self._write_empty_file(output_path)
                return

            print(f"LZ77: Чтение {original_size} байтов из {input_path}")

            window = SlidingWindow(self.window_size, self.lookahead_size)
            window.add_data(original_data)

            tokens = []
            total_compressed_size = 0

            while window.has_more_data():
                search_buffer = window.get_search_buffer()
                lookahead_buffer = window.get_lookahead_buffer()

                if not lookahead_buffer:
                    break

                offset, length = self.find_longest_match(search_buffer, lookahead_buffer)

                if length < len(lookahead_buffer):
                    next_char = lookahead_buffer[length]
                    advance_by = length + 1
                else:
                    next_char = 0
                    advance_by = length

                token = LZ77Token(offset, length, next_char)
                tokens.append(token)

                window.advance(advance_by)

                token_size = 2 + 1 + 1  # offset (2 байта) + length (1 байт) + char (1 байт)
                total_compressed_size += token_size

            self._write_compressed_data(output_path, tokens, original_size)

            print(f"LZ77: Сжатие завершено. Токенов: {len(tokens)}")

        except Exception as e:
            print(f"LZ77 Ошибка сжатия: {e}")
            raise

    def decompress(self, input_path: str, output_path: str):
        try:
            with open(input_path, 'rb') as f:
                magic = f.read(6)
                if magic != b"LZ77\0\0":
                    raise ValueError("Не валидный LZ77 сжатый файл")

                window_size = int.from_bytes(f.read(2), 'big')
                lookahead_size = int.from_bytes(f.read(1), 'big')
                original_size = int.from_bytes(f.read(4), 'big')

                if original_size == 0:
                    with open(output_path, 'wb') as out_f:
                        out_f.write(b"")
                    return

                tokens = []
                while True:
                    token_data = f.read(4)
                    if not token_data or len(token_data) < 4:
                        break

                    offset = int.from_bytes(token_data[0:2], 'big')
                    length = token_data[2]
                    next_char = token_data[3]

                    tokens.append(LZ77Token(offset, length, next_char))

            decoded_data = bytearray()

            for token in tokens:
                if token.offset > 0:
                    start_pos = len(decoded_data) - token.offset
                    for i in range(token.length):
                        decoded_data.append(decoded_data[start_pos + i])

                if token.next_char != 0:
                    decoded_data.append(token.next_char)

            if len(decoded_data) != original_size:
                print(f"LZ77 Предупреждение: декодированы {len(decoded_data)} байтов, ожидалось {original_size}")

            with open(output_path, 'wb') as f:
                f.write(decoded_data)

            print(f"LZ77: Распаковка завершена. Декодировано {len(decoded_data)} байтов")

        except Exception as e:
            print(f"LZ77 Ошибка распаковки: {e}")
            raise

    def _write_empty_file(self, output_path: str):
        with open(output_path, 'wb') as f:
            f.write(b"LZ77\0\0")  # Магическое число + версия
            f.write((0).to_bytes(2, 'big'))  # window_size
            f.write((0).to_bytes(1, 'big'))  # lookahead_size
            f.write((0).to_bytes(4, 'big'))  # original_size

    def _write_compressed_data(self, output_path: str, tokens: list, original_size: int):
        with open(output_path, 'wb') as f:
            f.write(b"LZ77\0\0")  # Магическое число + версия
            f.write(self.window_size.to_bytes(2, 'big'))
            f.write(self.lookahead_size.to_bytes(1, 'big'))
            f.write(original_size.to_bytes(4, 'big'))

            for token in tokens:
                f.write(token.offset.to_bytes(2, 'big'))
                f.write(token.length.to_bytes(1, 'big'))
                f.write(token.next_char.to_bytes(1, 'big'))