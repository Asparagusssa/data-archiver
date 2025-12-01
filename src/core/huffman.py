import pickle
from src.models.huffman_models import Node, MinHeap
from src.utils.bit_io import BitWriter, BitReader

class HuffmanCompressor:
    def __init__(self):
        self.codes = {}
        self.reverse_codes = {}

    def build_frequency_table(self, data):
        frequency = {}
        for byte in data:
            frequency[byte] = frequency.get(byte, 0) + 1

        # Добавляем специальный символ для конца данных (EOF)
        # Это поможет при декодировании, чтобы не читать лишние биты
        frequency[256] = 1  # 256 - наш EOF маркер
        return frequency

    def build_huffman_tree(self, frequency):
        if not frequency:
            return None

        heap = MinHeap()

        for symbol, freq in frequency.items():
            heap.push(Node(freq, symbol))

        while heap.size() > 1:
            left = heap.pop()
            right = heap.pop()
            merged = Node(left.frequency + right.frequency, left=left, right=right)
            heap.push(merged)

        return heap.pop()

    def _build_codes_recursive(self, node, current_code):
        if node is None:
            return

        if node.symbol is not None:
            self.codes[node.symbol] = current_code
            self.reverse_codes[current_code] = node.symbol
        else:
            self._build_codes_recursive(node.left, current_code + "0")
            self._build_codes_recursive(node.right, current_code + "1")

    def build_codes(self, root):
        self.codes = {}
        self.reverse_codes = {}
        if root:
            self._build_codes_recursive(root, "")

    def serialize_tree(self, root):
        frequency = {}
        stack = [root]
        while stack:
            node = stack.pop()
            if node.symbol is not None:
                frequency[node.symbol] = node.frequency
            if node.right:
                stack.append(node.right)
            if node.left:
                stack.append(node.left)
        return frequency

    def compress(self, input_path, output_path):
        try:
            with open(input_path, 'rb') as f:
                original_data = f.read()

            original_size = len(original_data)

            if original_size == 0:
                with open(output_path, 'wb') as f:
                    f.write(b"HUFFMAN")  # Магическое число
                    f.write(b"\0")  # Версия формата
                    f.write((0).to_bytes(4, 'big'))
                    f.write((0).to_bytes(4, 'big'))
                print("Сжатие пустого файла завершено")
                return

            print(f"Прочитано {original_size} байтов из {input_path}")

            frequency = self.build_frequency_table(original_data)
            print(f"Таблица частоты построенная из {len(frequency)} символов")

            root = self.build_huffman_tree(frequency)
            if not root:
                raise ValueError("Ошибка построения дерева Хаффмана")

            self.build_codes(root)
            max_code_length = max(len(code) for code in self.codes.values())
            print(f"Таблица кодов построена. Максимальная длина кода: {max_code_length}")

            with open(output_path, 'wb') as f:
                f.write(b"HUFFMAN")  # Магическое число
                f.write(b"\0")  # Версия формата

                f.write(original_size.to_bytes(4, 'big'))

                tree_data = pickle.dumps(frequency)
                tree_size = len(tree_data)
                f.write(tree_size.to_bytes(4, 'big'))
                f.write(tree_data)

                bit_writer = BitWriter(f)
                total_bits = 0

                for byte in original_data:
                    code = self.codes[byte]
                    bit_writer.write_bits(code)
                    total_bits += len(code)

                eof_code = self.codes[256]
                bit_writer.write_bits(eof_code)
                total_bits += len(eof_code)

                padding_bits = bit_writer.flush()

                print(f"Биты заполнения: {padding_bits}")

        except Exception as e:
            print(f"Ошибка сжатия: {e}")
            raise

    def deserialize_tree(self, frequency):
        return self.build_huffman_tree(frequency)

    def decompress(self, input_path, output_path):
        try:
            with open(input_path, 'rb') as f:
                magic = f.read(7)
                if magic != b"HUFFMAN":
                    raise ValueError("Не валидный файл")

                version = f.read(1)  # Пропускаем версию

                original_size_data = f.read(4)
                if len(original_size_data) != 4:
                    raise ValueError("Неверный формат файла")
                original_size = int.from_bytes(original_size_data, 'big')

                if original_size == 0:
                    print("Пустой файл")
                    with open(output_path, 'wb') as out_file:
                        out_file.write(b"")
                    return

                tree_size_data = f.read(4)
                if len(tree_size_data) != 4:
                    raise ValueError("Неверный формат файла")
                tree_size = int.from_bytes(tree_size_data, 'big')

                tree_data = f.read(tree_size)
                if len(tree_data) != tree_size:
                    raise ValueError("Неверный формат файла")

                frequency = pickle.loads(tree_data)

                root = self.deserialize_tree(frequency)
                self.build_codes(root)

                print(f"Оригинальный размер: {original_size} байтов")
                print(f"Дерево восстановлено {len(frequency)} символов")

                bit_reader = BitReader(f)
                decoded_data = bytearray()
                current_node = root
                bits_decoded = 0

                while len(decoded_data) < original_size:
                    bit = bit_reader.read_bit()
                    if bit == -1:
                        if len(decoded_data) < original_size:
                            print(f"Предупреждение: EOF достигнуто но только {len(decoded_data)} байтов декодировано")
                        break

                    bits_decoded += 1

                    if bit == 0:
                        current_node = current_node.left
                    else:
                        current_node = current_node.right

                    if current_node and current_node.symbol is not None:
                        if current_node.symbol == 256:  # EOF маркер
                            break
                        decoded_data.append(current_node.symbol)
                        current_node = root

                if len(decoded_data) != original_size:
                    print(f"Предупреждение: декодировано {len(decoded_data)} байтов, ожидалось {original_size}")

                with open(output_path, 'wb') as out_file:
                    out_file.write(decoded_data)

                print(f"Распаковка завершена. Получено {len(decoded_data)} байтов")

        except Exception as e:
            print(f"Ошибка распаковки: {e}")
            raise