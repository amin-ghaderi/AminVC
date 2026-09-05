"""Run: python -m cloud_api"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8090"))
    uvicorn.run("cloud_api.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
