import asyncio
import pytest
import os
from typing import Dict, Any
from main import search_papers


@pytest.mark.asyncio
async def test_search_papers_with_query():
    """Test searching papers with a basic query."""
    query = "search_query=all:quantum computing"
    max_results = 5

    results = await search_papers(query, max_results=max_results)

    # Verify the structure of the results
    assert results is not None
    assert "feed_info" in results
    assert "papers" in results
    assert "count" in results
    assert isinstance(results["count"], int)
    assert results["count"] > 0
    assert len(results["papers"]) <= 5  # Should respect max_results

    # Verify paper structure
    paper = results["papers"][0]
    assert "arxiv_id" in paper
    assert "title" in paper
    assert "authors" in paper
    assert isinstance(paper["authors"], list)
    assert "summary" in paper
    assert "primary_category" in paper


@pytest.mark.asyncio
async def test_search_papers_with_category():
    """Test searching papers with a specific category."""
    query = "cat:cs.AI"
    results = await search_papers(query)

    assert results is not None
    assert "papers" in results
    assert results["count"] > 0

    # All papers should be in the cs.AI category
    for paper in results["papers"]:
        assert "cs.AI" in paper["categories"]


@pytest.mark.asyncio
async def test_search_papers_with_author():
    """Test searching for papers by a specific author."""
    query = "au:Feynman"
    results = await search_papers(query)

    assert results is not None
    assert "papers" in results

    # The author name should appear in at least one paper
    found = False
    for paper in results["papers"]:
        for author in paper["authors"]:
            if "Feynman" in author:
                found = True
                break

    assert found, "Author not found in any of the returned papers"


@pytest.mark.asyncio
async def test_search_papers_with_date_sort():
    """Test searching papers with sorting by date."""
    query = "all:quantum computing"

    results = await search_papers(query, sort_by="submittedDate", sort_order="ascending")

    assert results is not None
    assert "papers" in results
    assert results["count"] > 0


@pytest.mark.asyncio
async def test_search_papers_no_results():
    """Test searching with a query that should return no results."""
    # Using a very specific and unlikely query
    query = "thisisaveryunlikelysearchstringthatshouldhavenopapers12345xyz"

    results = await search_papers(query)

    assert results is not None
    assert "papers" in results
    assert results["count"] == 0
    assert len(results["papers"]) == 0
