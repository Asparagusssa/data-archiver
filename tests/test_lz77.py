"""
Тесты для алгоритма LZ77
"""
import unittest
import os
import tempfile
from src.core.lz77 import LZ77Compressor


class TestLZ77(unittest.TestCase):
    def setUp(self):
        self.compressor = LZ77Compressor(window_size=100, lookahead_size=10)

    def test_find_longest_match(self):
        search = b"abcabc"
        lookahead = b"abcd"
        offset, length = self.compressor.find_longest_match(search, lookahead)
        self.assertEqual(offset, 3)  # "abc" повторяется через 3 символа
        self.assertEqual(length, 3)  # длина совпадения 3

    def test_compress_decompress_cycle(self):
        test_data = b"abracadabra abracadabra abracadabra"

        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(test_data)
            input_path = input_file.name

        try:
            compressed_path = input_path + ".compressed"
            decompressed_path = input_path + ".decompressed"

            self.compressor.compress(input_path, compressed_path)

            self.compressor.decompress(compressed_path, decompressed_path)

            with open(decompressed_path, 'rb') as f:
                result = f.read()

            self.assertEqual(test_data, result)

        finally:
            for path in [input_path, compressed_path, decompressed_path]:
                if os.path.exists(path):
                    os.remove(path)


if __name__ == '__main__':
    unittest.main()