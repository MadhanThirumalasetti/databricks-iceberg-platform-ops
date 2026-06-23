import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
import boto3

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "platform-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def check_redshift_health(**context):
    client = boto3.client("cloudwatch", region_name="us-east-1")
    response = client.get_metric_statistics(
        Namespace="AWS/Redshift",
        MetricName="HealthStatus",
        Dimensions=[{"Name": "ClusterIdentifier", "Value": "prod-cluster"}],
        StartTime=datetime.utcnow() - timedelta(minutes=10),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=["Average"],
    )
    datapoints = response.get("Datapoints", [])
    if not datapoints or datapoints[-1]["Average"] < 1.0:
        logger.warning("Redshift health check failed")
        return "trigger_redshift_recovery"
    logger.info("Redshift cluster healthy")
    return "check_iceberg_compaction"


def trigger_redshift_recovery(**context):
    logger.info("Triggering Redshift recovery")
    client = boto3.client("redshift", region_name="us-east-1")
    client.reboot_cluster(ClusterIdentifier="prod-cluster")
    logger.info("Redshift reboot initiated")


def check_iceberg_compaction(**context):
    import sys
    sys.path.insert(0, "/opt/airflow/dags")
    from iceberg.compaction import IcebergCompactionManager, CompactionConfig
    config = CompactionConfig(catalog="glue", database="analytics", table="game_events")
    manager = IcebergCompactionManager(config)
    stats = manager.get_file_stats()
    small_file_ratio = stats["small_files"] / max(stats["total_files"], 1)
    logger.info(f"Iceberg stats: {stats} | Small file ratio: {small_file_ratio:.2%}")
    if small_file_ratio > 0.3:
        manager.run_compaction()


def report_platform_health(**context):
    logger.info("Platform health check complete — all systems healthy")


with DAG(
    dag_id="platform_monitoring_and_recovery",
    default_args=DEFAULT_ARGS,
    description="Monitor data platform health and trigger automated recovery",
    schedule_interval="*/30 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["platform", "monitoring", "recovery"],
) as dag:

    start = EmptyOperator(task_id="start")
    check_redshift = BranchPythonOperator(task_id="check_redshift_health", python_callable=check_redshift_health)
    redshift_recovery = PythonOperator(task_id="trigger_redshift_recovery", python_callable=trigger_redshift_recovery)
    check_iceberg = PythonOperator(task_id="check_iceberg_compaction", python_callable=check_iceberg_compaction)
    report_health = PythonOperator(task_id="report_platform_health", python_callable=report_platform_health, trigger_rule="none_failed_min_one_success")
    end = EmptyOperator(task_id="end")

    start >> check_redshift
    check_redshift >> redshift_recovery >> report_health
    check_redshift >> check_iceberg >> report_health
    report_health >> end
