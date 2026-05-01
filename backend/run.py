"""Development server entry point.

Pass ``loop="asyncio"`` so uvicorn calls
``asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())``
before starting, which is required for psycopg3 async on Windows.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        loop="asyncio",
        reload=False,
    )
