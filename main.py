# ABOUTME: MCP server for KevoDB using the Python SDK
# ABOUTME: Exposes KevoDB operations as MCP tools

from fastmcp import FastMCP
from kevo import Client as KevoClient, ClientOptions, ScanOptions, BatchOperation
from pydantic import BaseModel
from typing import Dict, List, Optional, Union
import logging
import os
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('kevo_mcp_server.log')
    ]
)
logger = logging.getLogger('kevo_mcp')

# Initialize FastMCP server
mcp = FastMCP("KevoMCP")

# Initialize KevoDB client
host = os.getenv("KEVO_HOST", "localhost")
port = os.getenv("KEVO_PORT", "50051")
kevo_client = KevoClient(ClientOptions(endpoint=f"{host}:{port}"))

# Models for request/response data


class KeyValue(BaseModel):
    key: str
    value: str


class ScanRequest(BaseModel):
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    start_key: Optional[str] = None
    end_key: Optional[str] = None
    limit: Optional[int] = None
    reverse: bool = False


@mcp.tool()
def connect() -> bool:
    """Connect to the KevoDB server"""
    logger.info("Attempting to connect to KevoDB server")
    try:
        kevo_client.connect()
        logger.info("Successfully connected to KevoDB server")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to KevoDB server: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


@mcp.tool()
def get(key: str) -> Dict[str, Union[str, bool]]:
    """Get a value by key from KevoDB"""
    logger.info(f"GET operation started for key: {key[:10]}...")

    try:
        # Convert string key to bytes
        logger.debug(f"Converting key to bytes: {key[:30]}...")
        key_bytes = key.encode('utf-8')
        logger.debug(f"Key length: {len(key_bytes)} bytes")

        logger.info("Sending GET request to KevoDB for key")
        value, found = kevo_client.get(key_bytes)

        if found:
            logger.info(f"Key found, value length: {len(value)} bytes")
            # Convert bytes value to string for JSON transport
            decoded_value = value.decode('utf-8')
            logger.debug(f"Decoded value length: {len(decoded_value)}")
            return {"value": decoded_value, "found": True}
        else:
            logger.info("Key not found")
            return {"value": "", "found": False}
    except Exception as e:
        logger.error(f"GET operation failed with error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return {"value": "", "found": False, "error": str(e)}


@mcp.tool()
def put(key: str, value: str) -> bool:
    """Store a key-value pair in KevoDB"""
    logger.info(f"PUT operation started for key: {key[:10]}...")

    try:
        # Convert string key/value to bytes directly
        logger.debug(f"Converting key to bytes: {key[:30]}...")
        key_bytes = key.encode('utf-8')
        logger.debug(f"Key length: {len(key_bytes)} bytes")

        logger.debug(f"Converting value to bytes: {value[:30]}...")
        value_bytes = value.encode('utf-8')
        logger.debug(f"Value length: {len(value_bytes)} bytes")

        logger.info(
            f"Sending PUT request to KevoDB for key length: {len(key_bytes)}, value length: {len(value_bytes)}")
        kevo_client.put(key_bytes, value_bytes)
        logger.info("PUT operation completed successfully")
        return True
    except Exception as e:
        logger.error(f"PUT operation failed with error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")

        # Log the key/value details that caused the error
        try:
            logger.debug(f"Failed key: {key}")
            logger.debug(f"Failed value: {value[:100]}")
        except Exception as log_e:
            logger.error(f"Error while logging key/value: {str(log_e)}")

        return False


@mcp.tool()
def delete(key: str) -> bool:
    """Delete a key-value pair from KevoDB"""
    logger.info(f"DELETE operation started for key: {key[:10]}...")

    try:
        logger.debug(f"Converting key to bytes: {key[:30]}...")
        key_bytes = key.encode('utf-8')
        logger.debug(f"Key length: {len(key_bytes)} bytes")

        kevo_client.delete(key_bytes)
        logger.info("DELETE operation completed successfully")
        return True
    except Exception as e:
        logger.error(f"DELETE operation failed with error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


@mcp.tool()
def scan(scan_options: ScanRequest) -> List[Dict[str, str]]:
    """Scan keys in KevoDB with options"""
    logger.info("SCAN operation started with options")

    try:
        results = []
        logger.info("Executing scan operation")

        # Create proper ScanOptions object from our ScanRequest model
        from kevo import ScanOptions
        options = ScanOptions(
            prefix=scan_options.prefix.encode('utf-8') if scan_options.prefix else None,
            suffix=scan_options.suffix.encode('utf-8') if scan_options.suffix else None,
            start_key=scan_options.start_key.encode('utf-8') if scan_options.start_key else None,
            end_key=scan_options.end_key.encode('utf-8') if scan_options.end_key else None,
            limit=scan_options.limit if scan_options.limit else 0
        )

        for kv in kevo_client.scan(options):
            try:
                # Decode bytes to strings
                key_str = kv.key.decode('utf-8')
                value_str = kv.value.decode('utf-8')

                results.append({
                    "key": key_str,
                    "value": value_str
                })
            except UnicodeDecodeError:
                logger.warning(
                    "Found binary data that couldn't be decoded as UTF-8, skipping")
                # Skip binary data that can't be decoded as UTF-8
                continue

        logger.info(f"Scan completed, found {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"SCAN operation failed with error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return []


@mcp.tool()
def batch_write(operations: List[str]) -> bool:
    """Perform multiple operations in a batch.

    Each operation should be a string in one of these formats:
    - "put key value" - Store a key-value pair
    - "delete key" - Delete a key

    Example:
        batch_write([
            "put user:123 {\"name\": \"John\"}",
            "delete user:456"
        ])
    """
    logger.info(
        f"BATCH_WRITE operation started with {len(operations)} operations")

    try:
        batch_ops: BatchOperation = []
        for i, op_str in enumerate(operations):
            try:
                # Split the operation string into parts
                parts = op_str.split(maxsplit=2)
                op_type = parts[0].lower()

                logger.debug(
                    f"Processing operation {i+1}/{len(operations)}: {op_str[:50]}...")

                if op_type == "put" and len(parts) == 3:
                    op = BatchOperation(
                        op_type=BatchOperation.Type.PUT,
                        key=parts[1].encode('utf-8'),
                        value=parts[2].encode('utf-8'),
                    )
                    logger.debug(
                        f"PUT - Key length: {len(op.key)} bytes, Value length: {len(op.value)} bytes")
                    batch_ops.append(op)
                elif op_type == "delete" and len(parts) == 2:
                    op = BatchOperation(
                        op_type=BatchOperation.Type.DELETE,
                        key=parts[1].encode('utf-8'),
                    )
                    logger.debug(f"DELETE - Key length: {len(op.key)} bytes")
                    batch_ops.append(op)
                else:
                    logger.warning(
                        f"Invalid operation format: {op_str[:50]}...")
                    raise ValueError(
                        f"Invalid operation format. Must be 'put key value' or 'delete key'")

            except Exception as e:
                logger.error(f"Error processing operation {i+1}: {str(e)}")
                raise ValueError(
                    f"Failed to process operation {i+1}: {str(e)}")

        if not batch_ops:
            logger.warning("No valid operations to process")
            return False

        logger.info(
            f"Sending batch with {len(batch_ops)} operations to KevoDB")
        kevo_client.batch_write(batch_ops)
        logger.info("Batch write completed successfully")
        return True
    except Exception as e:
        logger.error(f"BATCH_WRITE operation failed with error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


@mcp.tool()
def get_stats() -> Dict:
    """Get database statistics"""
    try:
        stats = kevo_client.get_stats()
        return stats.__dict__
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def begin_transaction() -> str:
    """Begin a new transaction and return transaction ID"""
    try:
        # Store transaction in a dict to keep track of it
        tx = kevo_client.begin_transaction()
        # Generate a unique ID for this transaction
        import uuid
        tx_id = str(uuid.uuid4())

        # Store transaction in a global variable (in a real app, use a proper store)
        # This is just a simple example - in production, use a proper transaction store
        if not hasattr(begin_transaction, "transactions"):
            begin_transaction.transactions = {}

        begin_transaction.transactions[tx_id] = tx
        logger.info(f"Transaction started with ID: {tx_id}")
        return tx_id
    except Exception as e:
        logger.error(f"Failed to begin transaction: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return ""


@mcp.tool()
def commit_transaction(tx_id: str) -> bool:
    """Commit a transaction by ID"""
    try:
        if not hasattr(begin_transaction, "transactions"):
            return False

        tx = begin_transaction.transactions.get(tx_id)
        if not tx:
            return False

        tx.commit()
        del begin_transaction.transactions[tx_id]
        return True
    except Exception as e:
        return False


@mcp.tool()
def rollback_transaction(tx_id: str) -> bool:
    """Roll back a transaction by ID"""
    try:
        if not hasattr(begin_transaction, "transactions"):
            return False

        tx = begin_transaction.transactions.get(tx_id)
        if not tx:
            return False

        tx.rollback()
        del begin_transaction.transactions[tx_id]
        return True
    except Exception as e:
        return False


@mcp.tool()
def tx_put(tx_id: str, key: str, value: str) -> bool:
    """Store a key-value pair within a transaction"""
    logger.info(
        f"TX_PUT operation started for transaction: {tx_id}, key: {key[:10]}...")

    try:
        if not hasattr(begin_transaction, "transactions"):
            logger.error("Transaction store not initialized")
            return False

        tx = begin_transaction.transactions.get(tx_id)
        if not tx:
            logger.error(f"Transaction not found with ID: {tx_id}")
            return False

        # Convert string to bytes
        key_bytes = key.encode('utf-8')
        value_bytes = value.encode('utf-8')
        logger.debug(
            f"Key length: {len(key_bytes)} bytes, Value length: {len(value_bytes)} bytes")

        tx.put(key_bytes, value_bytes)
        logger.info("TX_PUT operation completed successfully")
        return True
    except Exception as e:
        logger.error(f"TX_PUT operation failed with error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


@mcp.tool()
def tx_get(tx_id: str, key: str) -> Dict[str, Union[str, bool]]:
    """Get a value by key within a transaction"""
    logger.info(
        f"TX_GET operation started for transaction: {tx_id}, key: {key[:10]}...")

    try:
        if not hasattr(begin_transaction, "transactions"):
            logger.error("Transaction store not initialized")
            return {"value": "", "found": False}

        tx = begin_transaction.transactions.get(tx_id)
        if not tx:
            logger.error(f"Transaction not found with ID: {tx_id}")
            return {"value": "", "found": False}

        # Convert string to bytes
        key_bytes = key.encode('utf-8')
        logger.debug(f"Key length: {len(key_bytes)} bytes")

        value, found = tx.get(key_bytes)

        if found:
            # Convert bytes to string
            value_str = value.decode('utf-8')
            logger.info(
                f"Key found, value length: {len(value_str)} characters")
            return {"value": value_str, "found": True}
        else:
            logger.info("Key not found in transaction")
            return {"value": "", "found": False}
    except Exception as e:
        logger.error(f"TX_GET operation failed with error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return {"value": "", "found": False, "error": str(e)}


@mcp.tool()
def tx_delete(tx_id: str, key: str) -> bool:
    """Delete a key-value pair within a transaction"""
    logger.info(
        f"TX_DELETE operation started for transaction: {tx_id}, key: {key[:10]}...")

    try:
        if not hasattr(begin_transaction, "transactions"):
            logger.error("Transaction store not initialized")
            return False

        tx = begin_transaction.transactions.get(tx_id)
        if not tx:
            logger.error(f"Transaction not found with ID: {tx_id}")
            return False

        # Convert string to bytes
        key_bytes = key.encode('utf-8')
        logger.debug(f"Key length: {len(key_bytes)} bytes")

        tx.delete(key_bytes)
        logger.info("TX_DELETE operation completed successfully")
        return True
    except Exception as e:
        logger.error(f"TX_DELETE operation failed with error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


@mcp.tool()
def cleanup() -> bool:
    """Close the KevoDB connection"""
    try:
        kevo_client.close()
        return True
    except Exception as e:
        return False


if __name__ == "__main__":
    logger.info("Starting KevoDB MCP server")

    # Attempt to connect to KevoDB when server starts
    try:
        logger.info("Attempting initial connection to KevoDB")
        kevo_client.connect()
        logger.info("Successfully connected to KevoDB")
        print("Successfully connected to KevoDB")
    except Exception as e:
        logger.error(f"Error connecting to KevoDB: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        print(f"Error connecting to KevoDB: {e}")
        print("Server will still start, but connections will need to be initialized")

    # Log client configuration
    logger.info(
        f"KevoDB client configured with endpoint: {kevo_client.options.endpoint}")

    # Run the MCP server
    logger.info("Starting MCP server")
    mcp.run()
    logger.info("MCP server stopped")
