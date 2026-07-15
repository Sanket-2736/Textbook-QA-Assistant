"""CLI entry point for app modules."""

import sys

if __name__ == "__main__":
    # Route to ingest module if ingest subcommand is called
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        # Remove 'ingest' from argv so click processes remaining args
        sys.argv.pop(1)
        from app.ingest import main
        main()
    else:
        print("Usage: python -m app.ingest --file <pdf_path> --index <index_name>")
        print("       python -m app.ingest --help")
