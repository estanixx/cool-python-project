import unittest
from backend.dal.errors import NotFoundError
from backend.dal.dictionary_dao import DictionaryDAO
from backend.tests import conftest


class TestDictionaryIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conftest.configure_test_env()
        if not conftest.floci_available():
            raise unittest.SkipTest("Floci DynamoDB not available")
        conftest.ensure_tables()

    def setUp(self):
        conftest.clear_table("Dictionary", "Word")
        self.dao = DictionaryDAO(conftest.dynamodb_resource())

    def test_create_and_read(self):
        created = self.dao.create("apple", "A fruit")
        self.assertEqual(created["Word"], "Apple")

        fetched = self.dao.read("apple")
        self.assertEqual(fetched["definition"], "A fruit")

    def test_read_missing_returns_not_found(self):
        with self.assertRaises(NotFoundError) as context:
            self.dao.read("missing")
        self.assertIn("not found", str(context.exception))
