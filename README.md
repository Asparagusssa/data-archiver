# Примеры команд сжатия
```bash
.venv/bin/python run.py compress tests/test_files/sample.txt output.txt -s
.venv/bin/python run.py compress tests/test_files/sample.txt output.txt -s -a=huffman
.venv/bin/python run.py compress tests/test_files/sample.txt output.txt -s -a=rle
.venv/bin/python run.py compress tests/test_files/sample.txt output.txt -s -a=lz77
```

# Пример команды распаковки
```bash
.venv/bin/python run.py decompress output.txt result.txt
```

# Пример команды сравнения
```bash
.venv/bin/python run.py compare tests/test_files/sample.txt
```
