# arXiv Helper MCP Server

A Model Context Protocol (MCP) server that enables Claude Desktop to search for
scientific papers on arXiv. This server acts as a bridge between Claude and the
arXiv API, allowing Claude to search, filter, and retrieve academic papers
directly.

## Features

- **Search papers** by title, author, abstract, category, and more
- **Filter results** using arXiv's powerful query syntax
- **Sort papers** by relevance, submission date, or update date
- **View paper details** including abstracts, authors, and publication links
- **Support for pagination** to browse through large result sets

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) for dependency management
- Claude Desktop application

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency
management.

```bash
# Clone this repository (if you haven't already)
git clone https://github.com/aarangop/arxiv-mcp.git
cd arxiv_mcp
```

### Install astral uv

```bash
# Install uv if you haven't already
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh

```

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install dependencies

```bash
# Install dependencies using uv
uv add
uv add --dev
```

If you don't have uv installed, you can install it following the
[official documentation](https://github.com/astral-sh/uv#installation).

## Usage

Run the server manually:

```bash
python main.py
```

## Setting up with Claude Desktop

To add this arXiv helper to Claude Desktop, you need to modify the Claude
Desktop configuration file.

The configuration file is typically located at:

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Add the following section to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "arxiv_assistant": {
      "command": "/path/to/your/uv",
      "args": [
        "--directory",
        "/path/to/your/arxiv_mcp/folder",
        "run",
        "main.py"
      ]
    }
  }
}
```

Replace the paths with the actual paths on your system:

- `/path/to/your/uv` - The path to your uv executable (e.g.,
  `/Users/username/.local/bin/uv`)
- `/path/to/your/arxiv_mcp/folder` - The full path to this repository folder

### Example Configuration

Here's an example of what your configuration might look like:

```json
{
  "mcpServers": {
    "arxiv_assistant": {
      "command": "/Users/username/.local/bin/uv",
      "args": ["--directory", "/path/to/arxiv_mcp/", "run", "main.py"]
    }
  }
}
```

After saving the changes to the configuration file, restart Claude Desktop for
the changes to take effect.

## Using arXiv Helper in Claude

Once the MCP server is set up with Claude Desktop, you can use the arXiv
functionality by asking Claude to:

- "Search for recent papers on machine learning"
- "Find papers by 'Yoshua Bengio' about deep learning"
- "Look for papers in the cs.AI category about transformers"
- "Show me papers on quantum computing published this year"

Claude will use the arXiv API to fetch relevant papers and display the results.

## Testing

The project includes two sets of tests:

1. Integration tests for the API client (`test_search_papers.py`)
2. Unit tests for the parsing functions (`test_parsing_functions.py`)

### Running the tests

Run all tests with uv:

```bash
uv run pytest
```

Run specific test files:

```bash
# Run the API integration tests
uv run pytest test_search_papers.py

# Run the parsing function unit tests
uv run pytest test_parsing_functions.py
```

Run tests with verbose output:

```bash
uv run pytest -v
```

## Troubleshooting

If you encounter issues:

1. Ensure your Claude configuration is correct
2. Verify that the arXiv API is accessible from your network
3. Use the included utility scripts:
   - `./show_logs.sh` - View Claude's MCP-related logs in real-time
   - `./inspect.sh` - Run the MCP inspector to debug the MCP server (requires
     npx)

## License

[MIT License](LICENSE) or specify your license information here.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

Thank you to arXiv for use of its open access interoperability!
