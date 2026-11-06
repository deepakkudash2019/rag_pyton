import unittest
from utils.text_utils import clean_text, split_text
from utils.pdf_utils import extract_pages

class UtilityTests(unittest.TestCase):
    def test_clean_text_normalizes_whitespace(self):
        self.assertEqual(clean_text(" a  b\r\n\r\n\r\nc "), "a b\n\nc")
    def test_split_text_has_overlap(self):
        chunks = split_text("abcdefghij" * 5, chunk_size=20, chunk_overlap=5)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(any(set(chunks[i]) & set(chunks[i+1]) for i in range(len(chunks)-1)))
    def test_split_validates_configuration(self):
        with self.assertRaises(ValueError): split_text("x", 5, 5)
    def test_text_extraction(self):
        self.assertEqual(extract_pages("note.txt", b"hello\nworld"), [(None, "hello\nworld")])
        with self.assertRaises(ValueError): extract_pages("bad.exe", b"x")

if __name__ == "__main__": unittest.main()

