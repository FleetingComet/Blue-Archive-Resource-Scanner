"""Small CLI to run the DataSyncManager without forcing the main app to include network calls.

Usage: python -m tools.sync_data
"""

import argparse

from utils.sync.data_sync_manager import DataSyncManager


def main():
    parser = argparse.ArgumentParser(
        description="Run data sync for local processed data files."
    )
    parser.add_argument(
        "--no-retries",
        dest="retries",
        action="store_const",
        const=1,
        default=3,
        help="Disable retries (set retries to 1)",
    )
    args = parser.parse_args()

    mgr = DataSyncManager()
    mgr.retries = args.retries
    mgr.retry_backoff = 1.0
    mgr.update_from_online()


if __name__ == "__main__":
    main()
