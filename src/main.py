"""
Главный модуль архиватора
"""
import argparse
import os
from src.core.huffman import HuffmanCompressor
from src.core.lz77 import LZ77Compressor
from src.core.combined import CombinedCompressor
from src.core.rle import RLECompressor
from src.utils.format_detector import detect_compression_format

def main():
    parser = argparse.ArgumentParser(description='Архиватор данных')
    parser.add_argument('action', choices=['compress', 'decompress', 'compare', 'analyze'])
    parser.add_argument('input_file')
    parser.add_argument('output_file', nargs='?', help='Выходной файл (Опционально)')
    parser.add_argument('--algorithm', '-a', choices=['huffman', 'lz77', 'combined', 'rle'],
                       default='combined', help='Алгоритм сжатия')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='Показать статистику сжатия')

    args = parser.parse_args()

    try:
        if args.action == 'compress':
            handle_compress(args)

        elif args.action == 'decompress':
            handle_decompress(args)

        elif args.action == 'compare':
            compare_algorithms(args.input_file)

        elif args.action == 'analyze':
            analyze_file(args.input_file)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


def handle_compress(args):
    if args.algorithm == 'huffman':
        compressor = HuffmanCompressor()
    elif args.algorithm == 'lz77':
        compressor = LZ77Compressor()
    elif args.algorithm == 'rle':
        compressor = RLECompressor()
    else:
        compressor = CombinedCompressor()

    if not args.output_file:
        args.output_file = args.input_file + '.compressed'

    compressor.compress(args.input_file, args.output_file)

    # Статистика
    if args.stats:
        original_size = os.path.getsize(args.input_file)
        compressed_size = os.path.getsize(args.output_file)
        ratio = (1 - compressed_size / original_size) * 100
        print(f"\nСтатистика сжатия:")
        print(f"Оригинальный размер: {original_size} bytes")
        print(f"Сжатый размер: {compressed_size} bytes")
        print(f"Коэффициент сжатия: {ratio:.2f}%")


def handle_decompress(args):
    detected_format = detect_compression_format(args.input_file)
    if detected_format:
        print(f"Определен формат: {detected_format}")
        args.algorithm = detected_format
    else:
        if args.input_file.endswith('.huff'):
            args.algorithm = 'huffman'
        elif args.input_file.endswith('.lz77'):
            args.algorithm = 'lz77'
        elif args.input_file.endswith('.combi'):
            args.algorithm = 'combined'
        elif args.input_file.endswith('.rle'):
            args.algorithm = 'rle'
        else:
            args.algorithm = 'combined'
            print("Формат не определен, используем комбинированный...")

    if args.algorithm == 'huffman':
        compressor = HuffmanCompressor()
    elif args.algorithm == 'lz77':
        compressor = LZ77Compressor()
    elif args.algorithm == 'rle':
        compressor = RLECompressor()
    else:
        compressor = CombinedCompressor()

    if not args.output_file:
        if args.input_file.endswith('.compressed'):
            args.output_file = args.input_file[:-11] + '.decompressed'
        else:
            args.output_file = args.input_file + '.decompressed'

    print(f"Распаковка используя {args.algorithm} алгоритм...")
    compressor.decompress(args.input_file, args.output_file)


def compare_algorithms(input_file):
    print(f"Сравнение алгоритмов сжатия для: {input_file}")
    print("-" * 60)

    algorithms = [
        ('RLE', RLECompressor()),
        ('Huffman', HuffmanCompressor()),
        ('LZ77', LZ77Compressor()),
        ('Combined', CombinedCompressor())
    ]

    original_size = os.path.getsize(input_file)
    print(f"Оригинальный размер: {original_size} байт\n")

    for name, compressor in algorithms:
        output_file = f"temp_{name.lower()}.compressed"
        try:
            compressor.compress(input_file, output_file)
            compressed_size = os.path.getsize(output_file)
            ratio = (1 - compressed_size / original_size) * 100

            print(f"{name:8} | {compressed_size:8} байт | {ratio:6.2f}%")

            # Очистка
            if os.path.exists(output_file):
                os.remove(output_file)

        except Exception as e:
            print(f"{name:8} | ОШИБКА: {e}")


def analyze_file(input_file):
    print(f"RLE Анализ для: {input_file}")
    print("-" * 40)

    try:
        with open(input_file, 'rb') as f:
            data = f.read()

        rle = RLECompressor()
        analysis = rle.analyze_efficiency(data)

        print(f"Размер файла: {analysis['original_size']:,} байт")
        print(f"Предполагаемый RLE размер: {analysis['compressed_size']:,} байт")
        print(f"Предполагаемый коэффициент сжатия: {analysis['compression_ratio']:.2f}%")
        print(f"Кол-во RLE пар: {analysis['num_pairs']:,}")
        print(f"Эффективность: {analysis['efficiency']}")

    except Exception as e:
        print(f"Ошибка анализа RLE: {e}")


if __name__ == "__main__":
    exit(main())
