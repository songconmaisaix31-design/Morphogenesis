"""Independent stdio research MCP entry point; no credentials or ORCA imports."""
import argparse
from pathlib import Path

from local_assets.paths import no_links
from swarm.research.models import HostConfig
from swarm.research.server import create_server
from swarm.research.service import ResearchService


def main() -> None:
    parser = argparse.ArgumentParser(description="Host-bound research MCP (stdio)")
    parser.add_argument("--config", required=True, type=Path, help="Absolute trusted host configuration JSON")
    args = parser.parse_args()
    if not args.config.is_absolute():
        parser.error("--config must be absolute")
    no_links(args.config)
    config = HostConfig.model_validate_json(args.config.read_text(encoding="utf-8"))
    service = ResearchService(config)
    create_server(service).run(transport="stdio")


if __name__ == "__main__":
    main()
