import asyncio, hashlib, urllib.parse
from ecms.persistence.database.rest_session import db_session
from sqlalchemy import select
from ecms.persistence.models.project import ProjectConnector

async def fix():
    async with db_session() as s:
        stmt = select(ProjectConnector)
        result = await s.execute(stmt)
        conns = result.scalars().all()
        print(f"Found {len(conns)} connectors")
        for c in conns:
            if c.persist_path:
                print(f"  Skip (already set): {c.persist_path}")
                continue
            url = c.config.get("repo_url", "")
            if not url:
                print(f"  Skip: no repo_url")
                continue
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname or "unknown"
            path = parsed.path.strip("/").removesuffix(".git").replace("/", "-")
            name = f"{host}-{path}"
            hash_suffix = hashlib.md5(url.encode()).hexdigest()[:12]
            persist_path = f"/app/data/repos/{name}-{hash_suffix}"
            c.persist_path = persist_path
            print(f"  Set: {c.connector_type} -> {persist_path}")
        await s.flush()
        print("Done")

asyncio.run(fix())
