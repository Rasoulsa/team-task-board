import json
import logging
from pathlib import Path

from app.main import app

logger = logging.getLogger(__name__)


def main() -> None:
    schema = app.openapi()
    out = Path("openapi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %s", out)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
