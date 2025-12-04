import unittest
import os
import tempfile
from src.core.huffman import HuffmanCompressor


class TestHuffmanComplete(unittest.TestCase):
    def setUp(self):
        self.compressor = HuffmanCompressor()
        self.test_data = {
            "simple": b"aaaabbbccd",
            "text": b"this is a test text for huffman compression algorithm",
            "repeated": b"AAAAA" * 100,
            "binary": bytes(range(256)) * 2
        }

    def test_compress_decompress_cycle(self):
        for name, data in self.test_data.items():
            with self.subTest(data_type=name):
                with tempfile.NamedTemporaryFile(delete=False) as input_file:
                    input_file.write(data)
                    input_path = input_file.name

                try:
                    compressed_path = input_path + ".compressed"
                    decompressed_path = input_path + ".decompressed"

                    self.compressor.compress(input_path, compressed_path)

                    self.compressor.decompress(compressed_path, decompressed_path)

                    with open(decompressed_path, 'rb') as f:
                        result_data = f.read()

                    self.assertEqual(data, result_data,
                                     f"Данные повеждены: {name}")

                finally:
                    for path in [input_path, compressed_path, decompressed_path]:
                        if os.path.exists(path):
                            os.remove(path)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as empty_file:
            empty_path = empty_file.name

        try:
            compressed_path = empty_path + ".compressed"
            decompressed_path = empty_path + ".decompressed"

            self.compressor.compress(empty_path, compressed_path)

            self.assertTrue(os.path.exists(compressed_path))

            self.compressor.decompress(compressed_path, decompressed_path)

            self.assertTrue(os.path.exists(decompressed_path))
            self.assertEqual(os.path.getsize(decompressed_path), 0)

            with open(decompressed_path, 'rb') as f:
                content = f.read()
            self.assertEqual(content, b"")

        finally:
            for path in [empty_path, compressed_path, decompressed_path]:
                if os.path.exists(path):
                    os.remove(path)

    def test_single_byte(self):
        test_byte = b"X"
        with tempfile.NamedTemporaryFile(delete=False) as single_file:
            single_file.write(test_byte)
            single_path = single_file.name

        try:
            compressed_path = single_path + ".compressed"
            decompressed_path = single_path + ".decompressed"

            self.compressor.compress(single_path, compressed_path)
            self.compressor.decompress(compressed_path, decompressed_path)

            with open(decompressed_path, 'rb') as f:
                result = f.read()

            self.assertEqual(test_byte, result)

        finally:
            for path in [single_path, compressed_path, decompressed_path]:
                if os.path.exists(path):
                    os.remove(path)


if __name__ == '__main__':
    unittest.main()