import pickle
import math
from src.core.lz77 import LZ77Compressor
from src.core.huffman import HuffmanCompressor
from src.utils.bit_io import BitWriter, BitReader

class CombinedCompressor:
    def __init__(self):
        self.lz77 = LZ77Compressor()
        self.huffman = HuffmanCompressor()

    def compress(self, input_path: str, output_path: str):
        try:
            with open(input_path, 'rb') as f:
                original_data = f.read()

            original_size = len(original_data)
            if original_size == 0:
                self._write_empty_file(output_path)
                return

            print(f"Комбинированный: Чтение {original_size} байтов из {input_path}")

            # АНАЛИЗ ЭФФЕКТИВНОСТИ СЖАТИЯ
            analysis = self._analyze_compression_potential(original_data)
            print(f"Комбинированный: Анализ данных - Энтропия: {analysis['entropy']:.2f}, "
                  f"Коэффициент повторяемости: {analysis['repetition_ratio']:.2f}")

            if not self._should_use_combined(analysis, original_size):
                print("Комбинированный: Файл имеет слабый потенциал сжатия, используем только алгоритм Хаффмана...")
                self.huffman.compress(input_path, output_path)

                compressed_size = self._get_file_size(output_path)
                if not self._is_compression_effective(original_size, compressed_size):
                    print("Комбинированный: Сжатие не эффективно, сохраняем оригинальные данные...")
                    self._store_original_data(output_path, original_data)
                return

            print("Комбинированный: Этап 1 - Сжатие LZ77...")
            lz77_tokens = self._lz77_compress_data(original_data)

            serialized_size = len(lz77_tokens) * 4  # 4 байта на токен
            if serialized_size > original_size * 0.95:
                print("Комбинированный: LZ77 не эффективен, используем только алгоритм Хаффмана...")
                self.huffman.compress(input_path, output_path)
                return

            print("Комбинированный: Сериализация токенов LZ77...")
            serialized_tokens = self._serialize_tokens(lz77_tokens)

            print("Комбинированный: Этап 2 - Сжатие Хоффмана...")
            frequency = self.huffman.build_frequency_table(serialized_tokens)
            root = self.huffman.build_huffman_tree(frequency)
            self.huffman.build_codes(root)

            with open(output_path, 'wb') as f:
                # Заголовок
                f.write(b"COMBI")  # Магическое число
                f.write(b"\0")     # Версия
                f.write(original_size.to_bytes(4, 'big'))

                # Сохраняем параметры LZ77
                f.write(self.lz77.window_size.to_bytes(2, 'big'))
                f.write(self.lz77.lookahead_size.to_bytes(1, 'big'))

                # Сохраняем дерево Хаффмана
                tree_data = pickle.dumps(frequency)
                f.write(len(tree_data).to_bytes(4, 'big'))
                f.write(tree_data)

                # Кодируем данные алгоритмом Хаффмана
                bit_writer = BitWriter(f)

                # Кодируем сериализованные токены
                for byte in serialized_tokens:
                    code = self.huffman.codes[byte]
                    bit_writer.write_bits(code)

                # Добавляем маркер конца данных
                eof_code = self.huffman.codes[256]
                bit_writer.write_bits(eof_code)

                # Завершаем запись
                padding_bits = bit_writer.flush()

            # ФИНАЛЬНАЯ ПРОВЕРКА ЭФФЕКТИВНОСТИ
            compressed_size = self._get_file_size(output_path)
            if not self._is_compression_effective(original_size, compressed_size):
                print("Комбинированный: Финальное сжатие не эффективно, сохраняем оригинальный файл...")
                self._store_original_data(output_path, original_data)
            else:
                print(f"Комбинированный: Сжатие завершено")

        except Exception as e:
            print(f"Ошибка комбинированного сжатия: {e}")
            raise

    def _analyze_compression_potential(self, data: bytes) -> dict:
        if not data:
            return {'entropy': 0, 'repetition_ratio': 0}

        entropy = self._calculate_entropy(data)

        repetition_ratio = self._calculate_repetition_ratio(data)

        return {
            'entropy': entropy,
            'repetition_ratio': repetition_ratio,
            'size': len(data)
        }

    def _calculate_entropy(self, data: bytes) -> float:
        if len(data) == 0:
            return 0

        frequency = {}
        for byte in data:
            frequency[byte] = frequency.get(byte, 0) + 1

        entropy = 0
        total = len(data)
        for count in frequency.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy

    def _calculate_repetition_ratio(self, data: bytes) -> float:
        if len(data) < 2:
            return 0

        repeats = 0
        for i in range(1, len(data)):
            if data[i] == data[i-1]:
                repeats += 1

        return repeats / len(data)

    def _should_use_combined(self, analysis: dict, original_size: int) -> bool:
        if original_size < 1000:
            return False

        if analysis['entropy'] > 7.5:
            return False

        if analysis['repetition_ratio'] < 0.01  :
            return False

        return True

    def _is_compression_effective(self, original_size: int, compressed_size: int) -> bool:
        # Считаем эффективным если сжали хотя бы на 2%
        return compressed_size < original_size * 0.98

    def _store_original_data(self, output_path: str, data: bytes):
        with open(output_path, 'wb') as f:
            f.write(b"NOCOMPR")
            f.write(len(data).to_bytes(4, 'big'))
            f.write(data)

    def decompress(self, input_path: str, output_path: str):
        try:
            with open(input_path, 'rb') as f:
                magic = f.read(7)
                if magic == b"NOCOMPR":
                    original_size = int.from_bytes(f.read(4), 'big')
                    original_data = f.read(original_size)
                    with open(output_path, 'wb') as out_f:
                        out_f.write(original_data)
                    print(f"Комбинированный: Возвращен оригнальный файл ({original_size} байтов)")
                    return

                if magic[:5] != b"COMBI":
                    f.seek(0)
                    print("Комбинированный: Не комбинированный файл, пробуем алгоритм Хаффмана...")
                    self.huffman.decompress(input_path, output_path)
                    return

                version = magic[5] if len(magic) > 5 else 0
                if len(magic) < 7:
                    remaining_header = f.read(7 - len(magic))
                    magic = magic + remaining_header

                original_size = int.from_bytes(f.read(4), 'big')

                if original_size == 0:
                    with open(output_path, 'wb') as out_f:
                        out_f.write(b"")
                    return

                # Читаем параметры LZ77
                window_size = int.from_bytes(f.read(2), 'big')
                lookahead_size = int.from_bytes(f.read(1), 'big')

                # Восстанавливаем дерево Хаффмана
                tree_size = int.from_bytes(f.read(4), 'big')
                tree_data = f.read(tree_size)
                frequency = pickle.loads(tree_data)

                root = self.huffman.build_huffman_tree(frequency)
                self.huffman.build_codes(root)

                # Декодируем данные Хаффмана
                bit_reader = BitReader(f)
                decoded_bytes = bytearray()
                current_node = root

                while True:
                    bit = bit_reader.read_bit()
                    if bit == -1:
                        break

                    if bit == 0:
                        current_node = current_node.left
                    else:
                        current_node = current_node.right

                    if current_node and current_node.symbol is not None:
                        if current_node.symbol == 256:
                            break
                        decoded_bytes.append(current_node.symbol)
                        current_node = root

                # Десериализуем токены LZ77
                lz77_tokens = self._deserialize_tokens(decoded_bytes)

                # LZ77 декомпрессия
                decoded_data = self._lz77_decompress_data(lz77_tokens, original_size)

                with open(output_path, 'wb') as out_f:
                    out_f.write(decoded_data)

                print(f"Комбинированный: Распаковка завершена. Декодировано {len(decoded_data)} байтов")

        except Exception as e:
            print(f"Комбинированный Ошибка распаковки: {e}")
            raise

    def _lz77_compress_data(self, data: bytes) -> list:
        from src.models.lz77_models import SlidingWindow

        window = SlidingWindow(self.lz77.window_size, self.lz77.lookahead_size)
        window.add_data(data)

        tokens = []
        while window.has_more_data():
            search_buffer = window.get_search_buffer()
            lookahead_buffer = window.get_lookahead_buffer()

            if not lookahead_buffer:
                break

            offset, length = self.lz77.find_longest_match(search_buffer, lookahead_buffer)

            if length < len(lookahead_buffer):
                next_char = lookahead_buffer[length]
                advance_by = length + 1
            else:
                next_char = 0
                advance_by = length

            from src.models.lz77_models import LZ77Token
            tokens.append(LZ77Token(offset, length, next_char))
            window.advance(advance_by)

        return tokens

    def _lz77_decompress_data(self, tokens: list, original_size: int) -> bytes:
        decoded_data = bytearray()

        for token in tokens:
            if token.offset > 0:
                start_pos = len(decoded_data) - token.offset
                for i in range(token.length):
                    if start_pos + i < len(decoded_data):
                        decoded_data.append(decoded_data[start_pos + i])

            if token.next_char != 0:
                decoded_data.append(token.next_char)

        return bytes(decoded_data[:original_size])

    def _serialize_tokens(self, tokens: list) -> bytes:
        result = bytearray()
        for token in tokens:
            result.extend(token.offset.to_bytes(2, 'big'))
            result.append(token.length)
            result.append(token.next_char)
        return bytes(result)

    def _deserialize_tokens(self, data: bytes) -> list:
        from src.models.lz77_models import LZ77Token

        tokens = []
        for i in range(0, len(data), 4):
            if i + 4 <= len(data):
                offset = int.from_bytes(data[i:i+2], 'big')
                length = data[i+2]
                next_char = data[i+3]
                tokens.append(LZ77Token(offset, length, next_char))
        return tokens

    def _write_empty_file(self, output_path: str):
        with open(output_path, 'wb') as f:
            f.write(b"COMBI\0")
            f.write((0).to_bytes(4, 'big'))

    def _get_file_size(self, file_path: str) -> int:
        import os
        return os.path.getsize(file_path)