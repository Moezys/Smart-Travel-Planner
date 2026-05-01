"""Development server entry point.

psycopg3 async requires SelectorEventLoop on Windows; uvicorn 0.36+
uses get_loop_factory() which returns ProactorEventLoop by default.
We bypass that by calling asyncio.run() directly with the correct factory.
"""

import asyncio
import selectors
import sys

import uvicorn


def _selector_loop() -> asyncio.SelectorEventLoop:
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


if __name__ == "__main__":
    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )
    server = uvicorn.Server(config)

    if sys.platform == "win32":
        asyncio.run(server.serve(), loop_factory=_selector_loop)
    else:
        asyncio.run(server.serve())
