"""Run the API: `python -m marketpulse.api` (or `make api`).

Loads `.env` first so GEMINI_API_KEY / DATABASE_URL / JWT_SECRET_KEY are visible
before any provider or DB module reads the environment.
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import logging  # noqa: E402
import os  # noqa: E402

import uvicorn  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    host = os.environ.get("API_HOST", "0.0.0.0")  # noqa: S104 — containerised; bind all ifaces
    port = int(os.environ.get("API_PORT", "8000"))
    uvicorn.run("marketpulse.api.app:create_app", host=host, port=port, factory=True)


if __name__ == "__main__":
    main()
