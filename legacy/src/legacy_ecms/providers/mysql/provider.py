from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from legacy_ecms.core.uko import UKOMetadata, UKORelationship, UKOType, UniversalKnowledgeObject
from legacy_ecms.providers.base import KnowledgeProvider, ProviderStatus


@dataclass(frozen=True)
class MySQLConnectionConfig:
    host: str
    port: int
    user: str
    password: str
    database: str | None = None
    connect_timeout: int = 10


class MySQLProvider(KnowledgeProvider):
    """MySQL schema provider supporting snapshot and live connection modes."""

    provider_name = "mysql"
    provider_version = "0.2.0"

    def __init__(
        self,
        schemas: list[dict[str, Any]] | None = None,
        connection_factory: Any | None = None,
    ) -> None:
        self.schemas = schemas or []
        self.connection_config: MySQLConnectionConfig | None = None
        self.connection_factory = connection_factory
        self._authenticated = False
        self._sync_counts: dict[str, int] = {}
        self._last_sync_at: dict[str, datetime] = {}
        self._errors: dict[str, list[str]] = {}

    async def authenticate(self, credentials: dict[str, Any]) -> bool:
        if "schemas" in credentials:
            self.schemas = list(credentials["schemas"])
        if any(key in credentials for key in ("host", "user", "password", "database")):
            self.connection_config = MySQLConnectionConfig(
                host=credentials["host"],
                port=int(credentials.get("port", 3306)),
                user=credentials["user"],
                password=credentials["password"],
                database=credentials.get("database"),
                connect_timeout=int(credentials.get("connect_timeout", 10)),
            )
        self._authenticated = bool(self.schemas) or self.connection_config is not None
        return self._authenticated

    async def discover(self) -> list[str]:
        if self.connection_config is not None:
            return self._discover_live_schemas()
        return sorted({schema["name"] for schema in self.schemas if schema.get("name")})

    async def sync(
        self,
        resource_id: str,
        since: datetime | None = None,
    ) -> AsyncIterator[UniversalKnowledgeObject]:
        count = 0
        errors: list[str] = []
        try:
            schemas = self._load_live_schemas(resource_id) if self.connection_config else self.schemas
            for schema in schemas:
                if resource_id != "*" and schema.get("name") != resource_id:
                    continue
                for table in schema.get("tables", []):
                    count += 1
                    yield self._table_to_uko(schema["name"], table)
        except Exception as exc:
            errors.append(str(exc))
            raise
        finally:
            self._sync_counts[resource_id] = count
            self._last_sync_at[resource_id] = datetime.now(UTC)
            self._errors[resource_id] = errors

    async def validate(self) -> bool:
        if self.connection_config is not None:
            try:
                self._discover_live_schemas()
                return True
            except Exception:
                return False
        return self._authenticated or bool(self.schemas)

    async def get_status(self, resource_id: str) -> ProviderStatus:
        return ProviderStatus(
            provider_name=self.provider_name,
            resource_id=resource_id,
            is_authenticated=self._authenticated,
            last_sync_at=self._last_sync_at.get(resource_id),
            objects_synced=self._sync_counts.get(resource_id, 0),
            errors=self._errors.get(resource_id, []),
        )

    def _discover_live_schemas(self) -> list[str]:
        if self.connection_config is None:
            return []
        if self.connection_config.database:
            return [self.connection_config.database]
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                    ORDER BY schema_name
                    """
                )
                return [row["schema_name"] for row in cursor.fetchall()]

    def _load_live_schemas(self, resource_id: str) -> list[dict[str, Any]]:
        schema_names = self._discover_live_schemas() if resource_id == "*" else [resource_id]
        with self._connect() as connection:
            schemas: list[dict[str, Any]] = []
            for schema_name in schema_names:
                tables = self._load_tables(connection, schema_name)
                columns_by_table = self._load_columns(connection, schema_name)
                foreign_keys_by_table = self._load_foreign_keys(connection, schema_name)
                schemas.append(
                    {
                        "name": schema_name,
                        "tables": [
                            {
                                **table,
                                "columns": columns_by_table.get(table["name"], []),
                                "foreign_keys": foreign_keys_by_table.get(table["name"], []),
                            }
                            for table in tables
                        ],
                    }
                )
            return schemas

    def _load_tables(self, connection: Any, schema_name: str) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    table_name,
                    table_type,
                    create_time,
                    update_time,
                    table_comment
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
                """,
                (schema_name,),
            )
            return [
                {
                    "name": row["table_name"],
                    "table_type": row.get("table_type"),
                    "created_at": row.get("create_time"),
                    "updated_at": row.get("update_time") or row.get("create_time"),
                    "comment": row.get("table_comment"),
                }
                for row in cursor.fetchall()
            ]

    def _load_columns(self, connection: Any, schema_name: str) -> dict[str, list[dict[str, Any]]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    table_name,
                    column_name,
                    column_type,
                    is_nullable,
                    column_key,
                    column_default,
                    extra,
                    ordinal_position,
                    column_comment
                FROM information_schema.columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position
                """,
                (schema_name,),
            )
            columns_by_table: dict[str, list[dict[str, Any]]] = {}
            for row in cursor.fetchall():
                columns_by_table.setdefault(row["table_name"], []).append(
                    {
                        "name": row["column_name"],
                        "type": row["column_type"],
                        "nullable": row["is_nullable"] == "YES",
                        "key": row.get("column_key"),
                        "default": row.get("column_default"),
                        "extra": row.get("extra"),
                        "ordinal_position": row.get("ordinal_position"),
                        "comment": row.get("column_comment"),
                    }
                )
            return columns_by_table

    def _load_foreign_keys(self, connection: Any, schema_name: str) -> dict[str, list[dict[str, Any]]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    table_name,
                    column_name,
                    referenced_table_schema,
                    referenced_table_name,
                    referenced_column_name,
                    constraint_name
                FROM information_schema.key_column_usage
                WHERE table_schema = %s
                  AND referenced_table_name IS NOT NULL
                ORDER BY table_name, ordinal_position
                """,
                (schema_name,),
            )
            fks_by_table: dict[str, list[dict[str, Any]]] = {}
            for row in cursor.fetchall():
                fks_by_table.setdefault(row["table_name"], []).append(
                    {
                        "column": row["column_name"],
                        "references_schema": row["referenced_table_schema"],
                        "references_table": row["referenced_table_name"],
                        "references_column": row["referenced_column_name"],
                        "constraint_name": row.get("constraint_name"),
                    }
                )
            return fks_by_table

    def _connect(self) -> Any:
        if self.connection_config is None:
            raise RuntimeError("MySQL connection is not configured")
        if self.connection_factory is not None:
            return self.connection_factory(self.connection_config)

        import pymysql
        import pymysql.cursors

        return pymysql.connect(
            host=self.connection_config.host,
            port=self.connection_config.port,
            user=self.connection_config.user,
            password=self.connection_config.password,
            database=self.connection_config.database,
            connect_timeout=self.connection_config.connect_timeout,
            cursorclass=pymysql.cursors.DictCursor,
            charset="utf8mb4",
        )

    def _table_to_uko(self, schema_name: str, table: dict[str, Any]) -> UniversalKnowledgeObject:
        now = self._parse_datetime(table.get("updated_at")) or datetime.now(UTC)
        table_name = table["name"]
        columns = table.get("columns", [])
        foreign_keys = table.get("foreign_keys", [])
        ddl = table.get("ddl") or self._ddl_for_table(table_name, columns, foreign_keys)
        relationships = [
            UKORelationship(
                target_id=f"{fk.get('references_schema') or schema_name}.{fk['references_table']}",
                relationship="references",
                target_type=UKOType.TABLE,
                metadata=fk,
            )
            for fk in foreign_keys
        ]
        return UniversalKnowledgeObject(
            id=f"mysql:table:{schema_name}.{table_name}",
            type=UKOType.TABLE,
            name=f"{schema_name}.{table_name}",
            content=ddl,
            metadata=UKOMetadata(
                source=self.provider_name,
                source_id=f"{schema_name}.{table_name}",
                created_at=self._parse_datetime(table.get("created_at")) or now,
                modified_at=now,
                tags=["schema", "table"],
            ),
            relationships=relationships,
            raw_data={"schema": schema_name, **table},
        )

    def _ddl_for_table(
        self,
        table_name: str,
        columns: list[dict[str, Any]],
        foreign_keys: list[dict[str, Any]],
    ) -> str:
        lines = [f"CREATE TABLE {table_name} ("]
        definitions = [
            f"  `{column['name']}` {column.get('type', 'TEXT')}{' NOT NULL' if column.get('nullable') is False else ''}"
            for column in columns
        ]
        definitions.extend(
            f"  FOREIGN KEY ({fk['column']}) REFERENCES {fk['references_table']}({fk['references_column']})"
            for fk in foreign_keys
        )
        lines.append(",\n".join(definitions))
        lines.append(");")
        return "\n".join(lines)

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return None
