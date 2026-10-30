"""Small CLI to run the DataSyncManager without forcing the main app to include network calls.

Usage:
    python -m tools.sync_data
    python -m tools.sync_data --type items
    python -m tools.sync_data --no-retries
"""

import argparse

from src.utils.sync.data_sync_manager import DataSyncManager


def main():
    mgr = DataSyncManager()

    parser = argparse.ArgumentParser(
        description="Run data sync for local processed data files."
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=list(mgr.local_paths),
        help="Dataset to synchronize (default: all).",
    )
    parser.add_argument(
        "--no-retries",
        action="store_true",
        help="Attempt each download only once.",
    )
    args = parser.parse_args()

    if args.no_retries:
        mgr.retries = 1

    if args.type:
        mgr.remote_sources = {args.type: mgr.DEFAULT_ONLINE_URLS[args.type]}

    mgr.update_from_online()


if __name__ == "__main__":
    main()
