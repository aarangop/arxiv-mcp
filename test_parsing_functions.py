import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from main import parse_feed_to_dict, parse_entry_to_dict, format_paper


class TestParsingFunctions(unittest.TestCase):
    def test_parse_entry_to_dict(self):
        """Test parsing a feedparser entry into a dictionary."""
        # Create a mock entry
        entry = Mock()
        entry.id = "http://arxiv.org/abs/1234.5678"
        entry.title = "Test Paper Title\nwith line break"
        entry.summary = "This is a test summary\nwith line break"
        entry.authors = [Mock(name="Author One"), Mock(name="Author Two")]
        entry.published = "2023-01-15T12:00:00Z"

        # Create mock links
        entry.links = [
            {"rel": "alternate", "href": "http://arxiv.org/abs/1234.5678"},
            {"title": "pdf", "href": "http://arxiv.org/pdf/1234.5678"}
        ]

        # Create mock tags
        entry.tags = [{"term": "cs.AI"}, {"term": "cs.LG"}]

        # Call the function
        result = parse_entry_to_dict(entry)

        # Verify the results
        self.assertEqual(result["arxiv_id"], "1234.5678")
        self.assertEqual(result["title"], "Test Paper Title with line break")
        self.assertEqual(result["summary"],
                         "This is a test summary with line break")
        self.assertEqual(result["authors"], ["Author One", "Author Two"])
        self.assertEqual(result["categories"], ["cs.AI", "cs.LG"])
        self.assertEqual(result["primary_category"], "cs.AI")
        self.assertEqual(result["pdf_url"], "http://arxiv.org/pdf/1234.5678")
        self.assertEqual(result["abs_url"], "http://arxiv.org/abs/1234.5678")

        # Check if published date was parsed correctly
        self.assertTrue(isinstance(result["published"], str))

    def test_parse_entry_to_dict_missing_attributes(self):
        """Test parsing an entry with missing attributes."""
        # Create a minimalistic entry
        entry = Mock()
        entry.id = "simple_id"
        entry.title = "Simple Title"
        entry.summary = "Simple Summary"

        # No authors, links, or tags

        # Call the function
        result = parse_entry_to_dict(entry)

        # Verify the results
        self.assertEqual(result["arxiv_id"], "simple_id")
        self.assertEqual(result["title"], "Simple Title")
        self.assertEqual(result["summary"], "Simple Summary")
        self.assertEqual(result["authors"], [])
        self.assertEqual(result["categories"], [])
        self.assertIsNone(result["primary_category"])
        self.assertIsNone(result["pdf_url"])
        self.assertIsNone(result["abs_url"])

    def test_parse_feed_to_dict(self):
        """Test parsing a complete feed to dictionary."""
        # Create a mock feed
        feed = Mock()
        feed.feed = Mock(
            title="arXiv Query Results",
            updated="2023-01-15T12:00:00Z",
            opensearch_totalresults="100",
            opensearch_startindex="0",
            opensearch_itemsperpage="10"
        )

        # Create two mock entries
        entry1 = Mock()
        entry1.id = "http://arxiv.org/abs/1234.5678"
        entry1.title = "First Paper"
        entry1.summary = "First Summary"
        entry1.authors = [Mock(name="Author One")]
        entry1.published = "2023-01-15T12:00:00Z"
        entry1.links = []
        entry1.tags = []

        entry2 = Mock()
        entry2.id = "http://arxiv.org/abs/8765.4321"
        entry2.title = "Second Paper"
        entry2.summary = "Second Summary"
        entry2.authors = [Mock(name="Author Two")]
        entry2.published = "2023-01-16T12:00:00Z"
        entry2.links = []
        entry2.tags = []

        feed.entries = [entry1, entry2]

        # Call the function
        result = parse_feed_to_dict(feed)

        # Verify the results
        self.assertIn("feed_info", result)
        self.assertIn("papers", result)
        self.assertIn("count", result)

        self.assertEqual(result["feed_info"]["title"], "arXiv Query Results")
        self.assertEqual(result["feed_info"]["total_results"], 100)
        self.assertEqual(result["feed_info"]["start_index"], 0)
        self.assertEqual(result["feed_info"]["items_per_page"], 10)

        self.assertEqual(len(result["papers"]), 2)
        self.assertEqual(result["count"], 2)

        self.assertEqual(result["papers"][0]["title"], "First Paper")
        self.assertEqual(result["papers"][1]["title"], "Second Paper")

    def test_format_paper(self):
        """Test the format_paper function."""
        # Create a sample paper dictionary
        paper = {
            "arxiv_id": "1234.5678",
            "title": "Test Paper",
            "authors": ["Author One", "Author Two"],
            "published": "2023-01-15T12:00:00",
            "summary": "This is a test summary",
            "primary_category": "cs.AI"
        }

        # Call the function
        result = format_paper(paper)

        # Verify the output format
        expected_output = """
arXiv Id: 1234.5678
Paper Title: Test Paper
Authors: Author One, Author Two
Published: 2023-01-15T12:00:00
Summary: This is a test summary
Category: cs.AI
"""

        self.assertEqual(result, expected_output)


if __name__ == "__main__":
    unittest.main()
