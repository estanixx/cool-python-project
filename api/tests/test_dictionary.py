import unittest
from api.utils import Dictionary

class TestDictionary(unittest.TestCase):
    """Test cases for the Dictionary class."""
    def setUp(self):
        """Set up a dictionary for testing."""
        self.dictionary = Dictionary()

    def test_newentry_and_look(self):
        """Test adding a new entry to the dictionary and looking it up."""
        self.dictionary.newentry('apple', 'A fruit that grows on trees.')
        self.assertEqual(self.dictionary.look('apple'), 'A fruit that grows on trees.')

    def test_look_nonexistent_entry(self):
        """Test looking up a nonexistent entry in the dictionary."""
        self.assertEqual(self.dictionary.look('banana'), "Can't find entry for Banana")