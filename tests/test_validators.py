import unittest

from app.utils.validators import normalize_full_name, normalize_phone


class ValidatorsTest(unittest.TestCase):
    def test_normalizes_name(self):
        self.assertEqual(normalize_full_name("  Иван   Иванов  "), "Иван Иванов")

    def test_rejects_digits_in_name(self):
        with self.assertRaises(ValueError):
            normalize_full_name("Иван 2")

    def test_normalizes_phone(self):
        self.assertEqual(normalize_phone("+7 (999) 123-45-67"), "+79991234567")

    def test_rejects_short_phone(self):
        with self.assertRaises(ValueError):
            normalize_phone("123")


if __name__ == "__main__":
    unittest.main()

