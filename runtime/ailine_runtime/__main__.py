from __future__ import annotations

import os

import uvicorn


def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Use the new app factory via import string for uvicorn reload support
    uvicorn.run(
        "ailine_runtime.api.app:create_app",
        host=host,
        port=port,
        factory=True,
    )


if __name__ == "__main__":
    main()
