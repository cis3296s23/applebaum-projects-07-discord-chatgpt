import unittest
from src.client import chunkify

class TestMessageChunking(unittest.TestCase):
    """Unit tests for the client.chunkify method"""

    def test_empty_input(self):
        self.assertEqual(chunkify(""), [])

    def test_small_chunk(self):
        self.assertEqual(chunkify("Hello world!"), ["Hello world!"])

    def test_one_large_chunk(self):
        self.assertEqual(chunkify("a"*1899), ["a"*1899])

    def test_two_chunks(self):
        self.assertEqual(chunkify("a"*3800), ["a"*1900]*2)

    def test_many_chunks(self):
        self.assertEqual(chunkify("a"*28500), ["a"*1900]*15)

if __name__ == "__main__":
    unittest.main()