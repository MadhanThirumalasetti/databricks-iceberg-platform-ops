# Databricks & Iceberg Platform Operations

Enterprise data platform operations toolkit for managing Apache Iceberg data lakes on S3, Databricks workspaces with Unity Catalog, Redshift clusters, RDS/Aurora PostgreSQL, and AWS security controls.

Built from real-world platform engineering work across multi-TB production environments on AWS.

---

## What This Covers

| Area | Tools |
|---|---|
| Open Table Format | Apache Iceberg on S3 — compaction, snapshots, partitions, schema evolution |
| Lakehouse Platform | Databricks — Unity Catalog, cluster management, Delta Live Tables |
| Data Warehouse | AWS Redshift — cluster ops, user/group management, query tuning |
| Database Operations | RDS/Aurora PostgreSQL — pg_stat views, parameter groups, replication |
| AWS Security | IAM roles/policies, S3 bucket policies, least-privilege access controls |
| Monitoring & Recovery | Datadog alerts, Airflow-based automated recovery workflows |
| Infrastructure as Code | Terraform — repeatable, auditable AWS platform deployments |

---

## Repository Structure
databricks-iceberg-platform-ops/

├── iceberg/                    # Apache Iceberg table management

│   ├── compaction.py           # Automated compaction scheduling

│   ├── snapshot_manager.py     # Snapshot lifecycle and expiry

│   └── schema_evolution.py     # Schema evolution utilities

├── redshift/                   # Redshift cluster operations

│   ├── user_group_manager.py   # User/group provisioning automation

│   └── query_optimizer.sql     # Query tuning patterns and templates

├── databricks/                 # Databricks workspace administration

│   ├── unity_catalog_setup.py  # Unity Catalog access control config

│   └── cluster_autoscaling_config.json

├── aws_security/               # AWS IAM and S3 security

│   ├── iam_policy_templates/

│   │   └── least_privilege_policy.json

│   └── s3_bucket_policy.json

├── monitoring/                 # Monitoring and recovery automation

│   ├── datadog_alerts.py       # Datadog SLA alert configuration

│   └── airflow_recovery_dag.py # Automated incident recovery DAG

└── terraform/                  # Infrastructure as Code

└── platform_infra.tf       # AWS platform provisioning
---

## Tech Stack

- **Compute**: AWS EMR, Databricks (AWS), EC2
- **Storage**: AWS S3, Apache Iceberg, Delta Lake
- **Databases**: AWS Redshift, RDS/Aurora PostgreSQL, DynamoDB
- **Orchestration**: Apache Airflow, Databricks Workflows
- **Monitoring**: Datadog, CloudWatch
- **IaC**: Terraform, AWS CDK
- **Languages**: Python 3.x, SQL, Bash
- **CI/CD**: GitHub Actions, Jenkins

---

## Author

**Madhan Thirumalasetti**
Data Platform Engineer | AWS | Databricks | Apache Iceberg
[github.com/MadhanThirumalasetti](https://github.com/MadhanThirumalasetti)
