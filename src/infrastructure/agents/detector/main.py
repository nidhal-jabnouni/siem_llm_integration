from src.presentation.cli.commands import setup_argparse
from src.infrastructure.config.settings import load_config
from src.application.use_cases.index_logs import index_logs
from src.application.use_cases.search_indexed_logs import search_indexed_logs
from src.application.use_cases.enrich_logs import enrich_logs
from src.application.tools.logger import logger
import sys

def main():
    """Main function."""
    try:
        # Parse command-line arguments
        args = setup_argparse()
        
        # Load configuration
        config = load_config()
        
        # Determine command to run
        if args.command == "index":
            index_logs(config, args.log_file, args.chunk_size, args.chunk_overlap)
        elif args.command == "search":
            search_indexed_logs(config, args.query, args.k)
        elif args.command == "enrich":
            enrich_logs(config, args.batch_size, args.batch_delay)
        else:
            # Default behavior if no command is specified
            print("Security Log Analysis Tool")
            print("=" * 50)
            print("Available commands:")
            print("  index  - Index log files")
            print("  search - Search indexed logs")
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
