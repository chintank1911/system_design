import hashlib
from bitarray import bitarray


class BloomFilter:
    def __init__(self, size, hash_functions):
        self.size = size
        self.hash_functions = hash_functions
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)

    def add(self, item):
        for hash_func in self.hash_functions:
            hash_value = hash_func(item) % self.size
            self.bit_array[hash_value] = 1

    def check(self, item):
        for hash_func in self.hash_functions:
            hash_value = hash_func(item) % self.size
            if not self.bit_array[hash_value]:
                return False  # Definitely not in the set
        return True  # Probably in the set


# Example usage
if __name__ == "__main__":
    def hash_md5(item):
        return int(hashlib.md5(item.encode()).hexdigest(), 16)

    def hash_sha1(item):
        return int(hashlib.sha1(item.encode()).hexdigest(), 16)

    def hash_sha256(item):
        return int(hashlib.sha256(item.encode()).hexdigest(), 16)

    bloom = BloomFilter(size=1000, hash_functions=[hash_md5, hash_sha1, hash_sha256])

    # Add elements
    bloom.add("apple")
    bloom.add("banana")

    # Check membership
    print(bloom.check("apple"))  # Output: True (probably in the set)
    print(bloom.check("banana"))  # Output: True (probably in the set)
    print(bloom.check("cherry"))  # Output: False (definitely not in the set)
