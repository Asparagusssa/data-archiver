class BitWriter:
    def __init__(self, file):
        self.file = file
        self.current_byte = 0
        self.bit_count = 0

    def write_bit(self, bit):
        if bit not in (0, 1):
            raise ValueError("Бит должен быть 0 или 1")

        self.current_byte = (self.current_byte << 1) | bit
        self.bit_count += 1

        if self.bit_count == 8:
            self.file.write(bytes([self.current_byte]))
            self.current_byte = 0
            self.bit_count = 0

    def write_bits(self, bit_string):
        for bit_char in bit_string:
            self.write_bit(1 if bit_char == '1' else 0)

    def write_int(self, value, num_bits):
        if value < 0 or value >= (1 << num_bits):
            raise ValueError(f"Значение {value} не помещается в {num_bits} битах")

        for i in range(num_bits - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def flush(self):
        if self.bit_count > 0:
            self.current_byte <<= (8 - self.bit_count)
            self.file.write(bytes([self.current_byte]))
            padding_bits = 8 - self.bit_count
            self.current_byte = 0
            self.bit_count = 0
            return padding_bits
        return 0


class BitReader:
    def __init__(self, file):
        self.file = file
        self.current_byte = 0
        self.bit_count = 0
        self.eof = False
        self.total_bits_read = 0

    def read_bit(self):
        if self.bit_count == 0:
            byte = self.file.read(1)
            if not byte:
                self.eof = True
                return -1  # EOF
            self.current_byte = byte[0]
            self.bit_count = 8

        self.bit_count -= 1
        self.total_bits_read += 1

        return (self.current_byte >> self.bit_count) & 1

    def read_bits(self, num_bits):
        result = 0
        for _ in range(num_bits):
            bit = self.read_bit()
            if bit == -1:
                return -1  # EOF
            result = (result << 1) | bit
        return result

    def read_bit_string(self, length):
        bits = []
        for _ in range(length):
            bit = self.read_bit()
            if bit == -1:
                break
            bits.append(str(bit))
        return ''.join(bits) if bits else ""

    def get_total_bits_read(self):
        return self.total_bits_read
