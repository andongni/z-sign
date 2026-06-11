import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=os.getenv("FASTAPI_RELOAD", "0") == "1",
    )
