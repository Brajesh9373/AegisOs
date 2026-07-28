import asyncio

from ecms.config import get_settings
from ecms.core.graph import GraphClient


async def main() -> None:
    graph = GraphClient(get_settings())
    await graph.initialize()
    await graph.close()
    print("FalkorDB indices and constraints initialized.")


if __name__ == "__main__":
    asyncio.run(main())
