import unittest
from api.utils import word_trick

class TestWordTrick(unittest.TestCase):
    """Test cases for the word_trick function."""
    def test_word_trick(self):
        """Test cases for the word_trick function."""
        self.assertEqual(word_trick("The quick brown fox jumps over the lazy dog"), "Tuos")
        self.assertEqual(word_trick("Hello World"), "Ho")
        self.assertEqual(word_trick("Python is great"), "Pse")
        self.assertEqual(word_trick("A B C D E F G"), "A")
        self.assertEqual(word_trick("This is a test"), "Tst")