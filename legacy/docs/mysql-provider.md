# MySQL Provider

The MySQL provider supports two modes:

- Snapshot mode for tests or pre-normalized schema payloads.
- Live mode using a MySQL-compatible connection and `information_schema`.

## Live Sync API

```http
POST /providers/mysql/sync
Content-Type: application/json

{
  "host": "localhost",
  "port": 3306,
  "user": "ecms_reader",
  "password": "password-value",
  "database": "billing",
  "connect_timeout": 10,
  "persist": true
}
```

The connector reads:

- `information_schema.tables`
- `information_schema.columns`
- `information_schema.key_column_usage`

It emits table UKOs with:

- table name and generated DDL
- column metadata
- foreign-key relationships
- source ID in the form `database.table`

## Required Database Permissions

Use a read-only account with permission to inspect metadata:

```sql
GRANT SELECT ON billing.* TO 'ecms_reader'@'%';
```

For some managed MySQL services, metadata visibility may require privileges on the target schema.

## Credential Handling

The password is accepted as a secret request field and is not returned in API responses, UKO metadata, or provider status.

## Persistence

Set `persist` to `true` to write generated episodes into Graphiti/FalkorDB. When omitted or `false`, the route runs as a dry run and returns counts only.
