import os
import sys
import logging
import contextlib
from fastmcp import FastMCP

# Protocol-safe logging to stderr.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("V4-MCP-Server")

# Ensure local imports resolve.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import run_pipeline_logic
except ImportError as exc:
    logger.error("Failed to import pipeline logic: %s", exc)
    run_pipeline_logic = None

mcp = FastMCP("Local-Forge-V4")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@mcp.tool()
def forge_request(user_prompt: str) -> str:
    """
    Triggers the V4 Engine pipeline.
    """
    if run_pipeline_logic is None:
        return "Pipeline unavailable: import failed"

    allow_network = _env_bool("V4_ALLOW_NETWORK", False)
    dry_run = _env_bool("V4_DRY_RUN", False)
    timeout = int(os.getenv("V4_TIMEOUT", "120"))
    retries = int(os.getenv("V4_RETRIES", "3"))

    logger.info("Processing MCP request. allow_network=%s dry_run=%s", allow_network, dry_run)

    try:
        # Redirect stdout to stderr to avoid MCP stdio corruption.
        with contextlib.redirect_stdout(sys.stderr):
            result = run_pipeline_logic(
                user_request=user_prompt,
                dry_run=dry_run,
                timeout=timeout,
                retries=retries,
                allow_network=allow_network,
            )
        return f"OK: {result}"
    except Exception as exc:
        logger.error("Pipeline error: %s", exc)
        return f"ERROR: {exc}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
