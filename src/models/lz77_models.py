from dataclasses import dataclass
from typing import Tuple

@dataclass
class LZ77Token:
    offset: int  # Смещение назад
    length: int  # Длина совпадения
    next_char: int  # Следующий символ

    def __repr__(self):
        return f"({self.offset}, {self.length}, {chr(self.next_char) if self.next_char < 128 else '0x' + format(self.next_char, '02x')})"


class SlidingWindow:

    def __init__(self, window_size: int, lookahead_size: int):
        self.window_size = window_size
        self.lookahead_size = lookahead_size
        self.data = bytearray()
        self.current_pos = 0

    def add_data(self, data: bytes):
        self.data.extend(data)

    def get_lookahead_buffer(self) -> bytes:
        end_pos = min(self.current_pos + self.lookahead_size, len(self.data))
        return bytes(self.data[self.current_pos:end_pos])

    def get_search_buffer(self) -> bytes:
        start_pos = max(0, self.current_pos - self.window_size)
        return bytes(self.data[start_pos:self.current_pos])

    def advance(self, length: int):
        self.current_pos += length

    def has_more_data(self) -> bool:
        return self.current_pos < len(self.data)