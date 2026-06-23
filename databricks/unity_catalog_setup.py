import logging
from dataclasses import dataclass
from typing import List
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import SecurableType, Privilege, PermissionsChange

logger = logging.getLogger(__name__)


@dataclass
class CatalogAccessConfig:
    principal: str
    catalog: str
    privileges: List[str]
    schema: str = None


class UnityCatalogAdmin:

    def __init__(self, workspace_url: str, token: str):
        self.client = WorkspaceClient(host=workspace_url, token=token)

    def grant_catalog_access(self, config: CatalogAccessConfig):
        changes = [PermissionsChange(
            principal=config.principal,
            add=[Privilege[p] for p in config.privileges]
        )]
        self.client.grants.update(
            securable_type=SecurableType.CATALOG,
            full_name=config.catalog,
            changes=changes
        )
        logger.info(f"Granted {config.privileges} on '{config.catalog}' to '{config.principal}'")

    def grant_schema_access(self, config: CatalogAccessConfig):
        full_name = f"{config.catalog}.{config.schema}"
        changes = [PermissionsChange(
            principal=config.principal,
            add=[Privilege[p] for p in config.privileges]
        )]
        self.client.grants.update(
            securable_type=SecurableType.SCHEMA,
            full_name=full_name,
            changes=changes
        )
        logger.info(f"Granted {config.privileges} on schema '{full_name}' to '{config.principal}'")

    def list_catalog_permissions(self, catalog: str):
        permissions = self.client.grants.get(
            securable_type=SecurableType.CATALOG,
            full_name=catalog
        )
        return permissions.privilege_assignments

    def revoke_access(self, config: CatalogAccessConfig):
        changes = [PermissionsChange(
            principal=config.principal,
            remove=[Privilege[p] for p in config.privileges]
        )]
        self.client.grants.update(
            securable_type=SecurableType.CATALOG,
            full_name=config.catalog,
            changes=changes
        )
        logger.info(f"Revoked {config.privileges} on '{config.catalog}' from '{config.principal}'")

    def create_catalog(self, name: str, comment: str = ""):
        catalog = self.client.catalogs.create(name=name, comment=comment)
        logger.info(f"Created catalog: {name}")
        return catalog


if __name__ == "__main__":
    admin = UnityCatalogAdmin(
        workspace_url="https://your-workspace.azuredatabricks.net",
        token="your-token"
    )
    config = CatalogAccessConfig(
        principal="analysts_group",
        catalog="production",
        privileges=["USE_CATALOG", "USE_SCHEMA", "SELECT"]
    )
    admin.grant_catalog_access(config)
