from __future__ import annotations
import argparse
from typing import Optional

def setup_argparse() -> argparse.Namespace:
    """Set up command-line arguments."""
    parser = argparse.ArgumentParser(description="Security Log Analysis Tool")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index log files")
    index_parser.add_argument("--log-file", type=str, help="Path to log file")
    index_parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size for splitting documents")
    index_parser.add_argument("--chunk-overlap", type=int, default=100, help="Chunk overlap for splitting documents")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search indexed logs")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument("--k", type=int, default=5, help="Number of results to return")
    
    # Enrich command
    enrich_parser = subparsers.add_parser("enrich", help="Enrich logs with LLM insights")
    enrich_parser.add_argument("--batch-size", type=int, default=5, help="Number of documents to process in each batch")
    enrich_parser.add_argument("--batch-delay", type=float, default=1.0, help="Delay between batches to avoid rate limiting")
    # Write CSV command
    write_csv_parser = subparsers.add_parser("write_csv", help="Write nested data to CSV")
    
    return parser.parse_args()