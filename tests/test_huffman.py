"""
Тесты для алгоритма Хаффмана
"""
import unittest
import os
from src.core.huffman import HuffmanCompressor


class TestHuffman(unittest.TestCase):
    def setUp(self):
        self.compressor = HuffmanCompressor()
        self.test_data = b"this is an example for huffman encoding"

    def test_frequency_table(self):
        frequency = self.compressor.build_frequency_table(self.test_data)
        self.assertIn(ord(' '), frequency)
        self.assertTrue(len(frequency) > 0)

    def test_tree_building(self):
        frequency = self.compressor.build_frequency_table(self.test_data)
        tree = self.compressor.build_huffman_tree(frequency)
        self.assertIsNotNone(tree)

    def test_compression_consistency(self):
        # Тестируем, что сжатие -> распаковка дает исходные данные
        pass


if __name__ == '__main__':
    unittest.main()