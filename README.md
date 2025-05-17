# KevoDB MCP Server

This project implements a [MCP (Multimodal Communication Protocol)](https://gofastmcp.com/) server for [KevoDB](https://github.com/KevoDB/kevo), allowing AI agents to interact with KevoDB using a standardized API.

## Features

- Exposes KevoDB operations through MCP tools
- Supports all core KevoDB functionality:
  - Basic key-value operations (get, put, delete)
  - Range, prefix, and suffix scans
  - Transactions
  - Batch operations
  - Database statistics
- Simple string-based API with UTF-8 encoding

## Prerequisites

- Python 3.8+
- Running KevoDB server (default: localhost:50051)
- FastMCP library
- Python-Kevo SDK

## Installation

1. Install dependencies:

```bash
pip install fastmcp python-kevo
```

2. Ensure KevoDB is running on localhost:50051 (or set the `KEVO_HOST` and `KEVO_PORT` environment variables to connect to a different endpoint)

## Usage

### Running the MCP Server

Start the MCP server:

```bash
python main.py
```

This will launch the MCP server on http://localhost:9000/mcp

You can configure the KevoDB connection using environment variables:
- `KEVO_HOST`: Hostname of the KevoDB server (default: "localhost")
- `KEVO_PORT`: Port of the KevoDB server (default: "50051")

Example:
```bash
KEVO_HOST=192.168.1.100 KEVO_PORT=5000 python main.py
```

### Using with AI Agents

AI agents that support MCP can connect to this server and use all exposed tools. The server provides the following tools:

| Tool | Description |
|------|-------------|
| `connect` | Connect to the KevoDB server |
| `get` | Get a value by key from KevoDB |
| `put` | Store a key-value pair in KevoDB |
| `delete` | Delete a key-value pair from KevoDB |
| `scan` | Scan keys in KevoDB with options |
| `batch_write` | Perform multiple operations in a batch |
| `get_stats` | Get database statistics |
| `begin_transaction` | Begin a new transaction and return transaction ID |
| `commit_transaction` | Commit a transaction by ID |
| `rollback_transaction` | Roll back a transaction by ID |
| `tx_put` | Store a key-value pair within a transaction |
| `tx_get` | Get a value by key within a transaction |
| `tx_delete` | Delete a key-value pair within a transaction |
| `cleanup` | Close the KevoDB connection |

## Integration with AI Applications

To use KevoDB with your AI application:

1. Start the KevoDB server
2. Start this MCP server
3. Configure your AI agent to connect to the MCP endpoint
4. The AI agent can now use all KevoDB operations through the MCP interface

## License

[MIT](https://opensource.org/licenses/MIT)
