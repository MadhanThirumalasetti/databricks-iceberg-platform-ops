import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from pyiceberg.catalog import load_catalog

logger = logging.getLogger(__name__)


@dataclass
class SnapshotPolicy:
    min_snapshots_to_keep: int = 5
    max_snapshot_age_hours: int = 168


class SnapshotManager:

    def __init__(self, catalog_name: str, database: str, table: str):
        self.catalog = load_catalog(catalog_name, **{"type": "glue"})
        self.table_identifier = f"{database}.{table}"

    def expire_snapshots(self, policy: SnapshotPolicy):
        table = self.catalog.load_table(self.table_identifier)
        expire_before = datetime.utcnow() - timedelta(hours=policy.max_snapshot_age_hours)
        expire_ts_ms = int(expire_before.timestamp() * 1000)
        snapshots = table.snapshots()
        logger.info(f"Total snapshots before expiry: {len(snapshots)}")
        result = (
            table.expire_snapshots()
            .expire_older_than(expire_ts_ms)
            .retain_last(policy.min_snapshots_to_keep)
            .commit()
        )
        logger.info(f"Expired: {result.deleted_data_files_count} data files removed")
        return result

    def list_snapshots(self):
        table = self.catalog.load_table(self.table_identifier)
        snapshots = table.snapshots()
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        return sorted([
            {
                "snapshot_id": s.snapshot_id,
                "timestamp": datetime.fromtimestamp(s.timestamp_ms / 1000),
                "age_hours": round((now_ms - s.timestamp_ms) / (1000 * 3600), 1),
                "operation": s.summary.get("operation", "unknown"),
                "total_records": s.summary.get("total-records", 0),
            }
            for s in snapshots
        ], key=lambda x: x["timestamp"], reverse=True)


if __name__ == "__main__":
    manager = SnapshotManager("glue", "analytics", "game_events")
    policy = SnapshotPolicy(min_snapshots_to_keep=5, max_snapshot_age_hours=168)
    snapshots = manager.list_snapshots()
    logger.info(f"Current snapshots: {len(snapshots)}")
    manager.expire_snapshots(policy)
