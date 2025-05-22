from datetime import datetime
import logging
import sys
from typing import Any, Dict, Optional
import feedparser
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# Initialize MCP server
mcp = FastMCP("arXiv_helper")

# Configure logging to go to stderr only (not stdout)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # This is crucial - forces logs to stderr
)
logger = logging.getLogger(__name__)

valid_sort_order = ["ascending", "descending"]
valid_sort_by = ["relevance", "lastUpdatedDate", "submittedDate"]

# API interface: http://export.arxiv.org/api/{method_name}?{parameters}
ARXIV_API_URL_BASE = "http://export.arxiv.org/api/query"


def construct_search_query(
    query: str = "",
    title: str = "",
    author: str = "",
    abstract: str = "",
    category: str = "",
    journal_ref: str = "",
    report_number: str = "",
    operator: str = "AND"
) -> str:
    """
    Construct arXiv search query from structured parameters or return raw query.

    If 'query' is provided, it takes precedence (raw query mode).
    Otherwise, constructs query from individual field parameters.
    """

    # If raw query provided, use it directly
    if query.strip():
        return query.strip()

    def format_field_value(value: str) -> str:
        """Format field value, adding quotes if necessary for exact phrase matching"""
        value = value.strip()
        if not value:
            return ""

        # If already properly quoted, return as-is
        if value.startswith('"') and value.endswith('"') and len(value) > 2:
            return value

        # Remove any existing quotes first to avoid double-quoting
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        # If contains spaces, special characters, or is a phrase, add quotes
        if ' ' in value or any(char in value for char in [':', '+', '-', '(', ')', '[', ']', 'AND', 'OR', 'NOT']):
            return f'"{value}"'

        # Single word, no quotes needed unless it's a reserved word
        if value.upper() in ['AND', 'OR', 'NOT']:
            return f'"{value}"'

        return value

    # Build query from structured fields
    query_parts = []

    if title:
        formatted_title = format_field_value(title)
        query_parts.append(f"ti:{formatted_title}")
    if author:
        formatted_author = format_field_value(author)
        query_parts.append(f"au:{formatted_author}")
    if abstract:
        formatted_abstract = format_field_value(abstract)
        query_parts.append(f"abs:{formatted_abstract}")
    if category:
        # Categories typically don't need quotes (e.g., cs.AI, math.CO)
        query_parts.append(f"cat:{category.strip()}")
    if journal_ref:
        formatted_jr = format_field_value(journal_ref)
        query_parts.append(f"jr:{formatted_jr}")
    if report_number:
        formatted_rn = format_field_value(report_number)
        query_parts.append(f"rn:{formatted_rn}")

    if not query_parts:
        raise ValueError(
            "Must provide either 'query' or at least one search field")

    # Join with specified operator - use spaces around AND/OR (httpx will handle URL encoding)
    constructed_query = f" {operator} ".join(query_parts)
    logger.debug(f"Constructed query from fields: {constructed_query}")

    return constructed_query


async def search_papers(
        query: str,
        start: int = 0,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "ascending"
) -> Optional[Dict[str, Any]]:
    """
    Make a request to the arXiv API.
    """
    logger.debug(
        f"Searching papers with query: '{query}', start: {start}, max_results: {max_results}")

    headers = {
        "User-Agent": "ArxivMCPClient/1.0",
        "Accept": "application/atom+xml"
    }

    params = {
        "search_query": query,
        "start": start,
        "sortBy": sort_by,
        "sortOrder": sort_order,
        "max_results": max_results
    }

    logger.debug(f"API request parameters: {params}")

    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Making request to {ARXIV_API_URL_BASE}")
            response = await client.get(
                ARXIV_API_URL_BASE,
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            logger.debug(f"Received response status {response.status_code}")
            feed = feedparser.parse(response.text)
            result = parse_feed_to_dict(feed)
            logger.info(f"Search found {result['count']} papers")
            return result
        except httpx.RequestError as e:
            logger.error(f"API request failed: {str(e)}", exc_info=True)
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(
                f"Error parsing API response: {str(e)}", exc_info=True)
            return {"error": f"Parsing failed: {str(e)}"}


def parse_feed_to_dict(feed) -> Dict:
    """Convert feedparser feed to structured dictionary"""

    # Extract feed metadata
    feed_info = {
        "title": getattr(feed.feed, "title", ""),
        "updated": getattr(feed.feed, "updated", ""),
        "total_results": int(getattr(feed.feed, "opensearch_totalresults", 0)),
        "start_index": int(getattr(feed.feed, "opensearch_startindex", 0)),
        "items_per_page": int(getattr(feed.feed, "opensearch_itemsperpage", 0))
    }

    # Extract papers
    papers = []
    for entry in feed.entries:
        paper = parse_entry_to_dict(entry)
        papers.append(paper)

    return {
        "feed_info": feed_info,
        "papers": papers,
        "count": len(papers)
    }


def parse_entry_to_dict(entry) -> Dict:
    """Convert a single feed entry to a paper dictionary"""

    # Extract arXiv ID from the entry ID
    arxiv_id = entry.id.split(
        '/abs/')[-1] if '/abs/' in entry.id else entry.id

    # Extract authors (feedparser v6 handles multiple authors correctly)
    authors = []
    if hasattr(entry, 'authors'):
        authors = [author.name for author in entry.authors]
    elif hasattr(entry, 'author'):
        authors = [entry.author]

    # Extract links
    pdf_link = None
    abs_link = None
    for link in entry.links:
        if 'href' not in link:
            continue
        if link.get('rel') == 'alternate':
            abs_link = link.get('href')
        elif link.get('title') == 'pdf':
            pdf_link = link.get('href')

    # Extract categories
    categories = []
    primary_category = None
    if hasattr(entry, 'tags'):
        categories = [tag['term'] for tag in entry.tags]
        if categories:
            primary_category = categories[0]  # First tag is primary

    # Parse published date
    published_date = None
    if hasattr(entry, 'published'):
        try:
            published_date = datetime.strptime(
                entry.published,
                "%Y-%m-%dT%H:%M:%SZ"
            ).isoformat()
        except:
            published_date = entry.published

    paper = {
        "arxiv_id": arxiv_id,
        "title": entry.title.replace('\n', ' ').strip(),
        "authors": authors,
        "published": published_date,
        "summary": entry.summary.replace('\n', ' ').strip(),
        "primary_category": primary_category,
        "categories": categories,
        "pdf_url": pdf_link,
        "abs_url": abs_link,
        "journal_ref": getattr(entry, 'arxiv_journal_ref', None),
        "comment": getattr(entry, 'arxiv_comment', None),
        "doi": getattr(entry, 'arxiv_doi', None)
    }

    return paper


def format_paper(paper: Dict) -> str:
    return f"""
arXiv Id: {paper['arxiv_id']}
Paper Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Published: {paper['published']}
Summary: {paper['summary']}
Category: {paper['primary_category']}
"""


@mcp.tool(name="paper_search",
          description="""Searches arXiv using its public API. 

You can search in two ways:
1. STRUCTURED SEARCH: Provide specific field parameters (title, author, abstract, category, etc.)
2. RAW QUERY: Provide a complete arXiv query string using their syntax

Field prefixes for raw queries: ti: (title), au: (author), abs: (abstract), cat: (category), jr: (journal reference), rn: (report number)

Examples:
- Structured: title="attention", category="cs.AI" 
- Raw query: "ti:attention AND cat:cs.AI"
- Complex: "cat:cs.AI AND submittedDate:[202301010000 TO 202312312359]"
""",
          annotations=ToolAnnotations(
              title="Paper Search",
              readOnlyHint=True
          ))
async def get_papers(
    # Raw query (takes precedence if provided)
    query: str = "",

    # Structured search fields
    title: str = "",
    author: str = "",
    abstract: str = "",
    category: str = "",
    journal_ref: str = "",
    report_number: str = "",

    # Boolean operator for structured fields
    operator: str = "AND",

    # Sorting and pagination
    sort_by: str = "relevance",
    sort_order: str = "descending",
    start: int = 0,
    max_results: int = 10
) -> str:
    """
    Query the arXiv API to find papers.

    Args:
        query: Raw arXiv query string (takes precedence if provided)
        title: Search in paper titles
        author: Search for specific author
        abstract: Search in paper abstracts  
        category: arXiv category (e.g., cs.AI, math.CO)
        journal_ref: Journal reference
        report_number: Report number
        operator: Boolean operator for structured fields (AND/OR)
        sort_by: Sort criteria (relevance, submittedDate, lastUpdatedDate)
        sort_order: Sort order (ascending, descending)
        start: Starting index for pagination
        max_results: Maximum number of results (1-30)
    """

    try:
        # Construct the search query
        search_query = construct_search_query(
            query=query,
            title=title,
            author=author,
            abstract=abstract,
            category=category,
            journal_ref=journal_ref,
            report_number=report_number,
            operator=operator
        )

        logger.info(f"Executing search with query: '{search_query}'")

        # Validate max_results
        if max_results > 30:
            max_results = 30
            logger.warning("max_results capped at 30")

        results = await search_papers(
            query=search_query,
            start=start,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order
        )

        if not results or "error" in results:
            error_msg = results.get(
                "error", "Unknown error") if results else "Failed to fetch papers"
            logger.error(f"Search failed: {error_msg}")
            return f"Error: {error_msg}"

        if "papers" not in results or results["count"] == 0:
            logger.info("No papers found for query")
            return "No papers found matching your search criteria."

        logger.info(f"Retrieved {results['count']} papers")

        # Format response
        total_results = results['feed_info']['total_results']
        response = f"Found {results['count']} papers (showing {start+1}-{start+results['count']} of {total_results} total results).\n\n"

        paper_summaries = [format_paper(paper) for paper in results['papers']]
        response += "\n---\n".join(paper_summaries)

        # Add pagination info if there are more results
        if start + results['count'] < total_results:
            response += f"\n\n--- More results available (use start={start + max_results} for next page) ---"

        return response

    except ValueError as e:
        logger.error(f"Invalid search parameters: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(
            f"Unexpected error in get_papers: {str(e)}", exc_info=True)
        return f"Error: An unexpected error occurred while searching papers."


if __name__ == "__main__":
    mcp.run(transport="stdio")
