import logging
from dataclasses import dataclass
from pyiceberg.catalog import load_catalog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CompactionConfig:
    catalog: str
    database: str
    table: str
    target_file_size_mb: int = 128
    min_file_size_mb: int = 32


class IcebergCompactionManager:

    def __init__(self, config: CompactionConfig):
        self.config = config
        self.catalog = load_catalog(config.catalog, **{"type": "glue"})

    def get_table(self):
        return self.catalog.load_table(
            f"{self.config.database}.{self.config.table}"
        )

    def run_compaction(self):
        logger.info(f"Starting compaction: {self.config.database}.{self.config.table}")
        table = self.get_table()
        from pyiceberg.table.rewrite import RewriteDataFilesAction
        action = RewriteDataFilesAction(
            table=table,
            options={
                "target-file-size-bytes": str(self.config.target_file_size_mb * 1024 * 1024),
                "min-file-size-bytes": str(self.config.min_file_size_mb * 1024 * 1024),
            },
        )
        result = action.execute()
        logger.info(f"Compaction complete. Rewritten: {result.rewritten_data_files_count}")
        return result

    def get_file_stats(self):
        table = self.get_table()
        files = list(table.scan().plan_files())
        sizes = [f.file.file_size_in_bytes / (1024 * 1024) for f in files]
        return {
            "total_files": len(files),
            "total_size_mb": round(sum(sizes), 2),
            "avg_file_size_mb": round(sum(sizes) /
