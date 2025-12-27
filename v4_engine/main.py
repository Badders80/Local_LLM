"""
V4 Engine Orchestrator - Single entry point for the AI pipeline.

Architecture:
    1. Architect (Groq Cloud) -> Creates execution plan
    2. Builder (Local GPU) -> Generates Python code
    3. Executor (Docker Sandbox) -> Runs code safely

Usage:
    python main.py "Create a weather app"
    python main.py "Build a todo list" --dry-run
    python main.py "Make a game" --timeout 300
"""

import sys
import time
import json
import argparse
from architect import Architect
from builder import Builder
from executor import Executor
from config import Config
from colorama import Fore, init

init(autoreset=True)


class Orchestrator:
    """
    Main controller that manages the three-stage pipeline:
    Planning -> Building -> Execution
    """

    def __init__(self):
        Config.validate()
        self.architect = Architect()
        self.builder = Builder()
        self.executor = Executor()

    def _retry(self, func, *args, stage_name: str, max_attempts: int = 3):
        """
        Retry logic with exponential backoff for handling transient failures.
        """
        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args)
            except Exception as e:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"{stage_name} failed after {max_attempts} attempts: {e}"
                    )
                wait = 0.5 * (2 ** (attempt - 1))
                print(
                    f"{Fore.YELLOW}WARN: {stage_name} attempt {attempt}/{max_attempts} "
                    f"failed, retrying in {wait:.1f}s..."
                )
                time.sleep(wait)

    def run(
        self,
        user_request: str,
        dry_run: bool = False,
        timeout: int = 120,
        retries: int = 3,
        allow_network: bool = False,
        exit_on_error: bool = True,
    ):
        """
        Execute the full pipeline.
        """
        print(f"\n{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}V4 ENGINE: STARTING PRODUCTION PIPELINE")
        print(f"{Fore.MAGENTA}{'='*60}")
        print(f"\n{Fore.CYAN}REQUEST: {user_request}\n")

        try:
            print(f"{Fore.CYAN}Stage 1: Planning...")
            plan = self._retry(
                self.architect.create_plan, user_request, stage_name="Planning", max_attempts=retries
            )
            print(f"{Fore.GREEN}OK: Plan created\n")

            plan_path = Config.ARTIFACTS_DIR / f"plan_{int(time.time())}.json"
            with open(plan_path, "w") as f:
                f.write(json.dumps(plan, indent=2))

            print(f"{Fore.CYAN}Stage 2: Building code...")
            artifact_path = self._retry(
                self.builder.execute_plan,
                plan,
                plan_path.name,
                allow_network,
                stage_name="Building",
                max_attempts=retries,
            )

            for _ in range(10):
                if artifact_path.exists():
                    break
                time.sleep(0.1)
            else:
                raise FileNotFoundError(
                    f"Builder reported {artifact_path} but file not found after verification"
                )

            print(f"{Fore.GREEN}OK: Code built: {artifact_path.name}\n")

            if dry_run:
                print(f"{Fore.YELLOW}Dry-run mode: Skipping sandbox execution")
                print(f"{Fore.YELLOW}Generated artifact: {artifact_path}")
                print(f"\n{Fore.MAGENTA}{'='*60}")
                print(f"{Fore.GREEN}DRY-RUN COMPLETE")
                print(f"{Fore.MAGENTA}{'='*60}\n")
                return artifact_path

            print(f"{Fore.CYAN}Stage 3: Entering sandbox...")
            self.executor.run_artifact(
                artifact_path.name, timeout=timeout, allow_network=allow_network
            )
            print(f"{Fore.GREEN}OK: Execution completed\n")

            print(f"{Fore.MAGENTA}{'='*60}")
            print(f"{Fore.GREEN}PIPELINE COMPLETE - ALL STAGES SUCCESSFUL")
            print(f"{Fore.MAGENTA}{'='*60}\n")
            return artifact_path

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Pipeline interrupted by user (Ctrl+C)")
            if exit_on_error:
                sys.exit(130)
            raise
        except Exception as e:
            print(f"\n{Fore.RED}{'='*60}")
            print(f"{Fore.RED}PIPELINE CRASHED")
            print(f"{Fore.RED}{'='*60}")
            print(f"{Fore.RED}Error: {type(e).__name__}")
            print(f"{Fore.RED}Details: {e}")
            print(f"{Fore.RED}{'='*60}\n")
            if exit_on_error:
                sys.exit(1)
            raise


def run_pipeline_logic(
    user_request: str,
    dry_run: bool = False,
    timeout: int = 120,
    retries: int = 3,
    allow_network: bool = False,
):
    engine = Orchestrator()
    artifact_path = engine.run(
        user_request=user_request,
        dry_run=dry_run,
        timeout=timeout,
        retries=retries,
        allow_network=allow_network,
        exit_on_error=False,
    )
    if artifact_path is None:
        return "No artifact produced"
    return str(artifact_path)


def main():
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        prog="v4-engine",
        description="V4 Engine Orchestrator - Build and run AI-generated code safely",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Create a weather app"
  python main.py "Build a calculator" --dry-run
  python main.py "Make a web scraper" --timeout 300
        """,
    )

    parser.add_argument(
        "prompt",
        nargs="*",
        help="Natural language description of what to build",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate plan and code only, skip sandbox execution",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Maximum execution time in seconds (default: 120)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Maximum retry attempts per stage (default: 3)",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow network access inside the sandbox (default: off)",
    )

    args = parser.parse_args()

    if args.prompt:
        prompt = " ".join(args.prompt)
    else:
        prompt = "Create a Python script that calculates the Fibonacci sequence up to 100."
        print(f"{Fore.YELLOW}WARN: No prompt provided, using default example\n")

    engine = Orchestrator()
    engine.run(
        user_request=prompt,
        dry_run=args.dry_run,
        timeout=args.timeout,
        retries=args.retries,
        allow_network=args.allow_network,
    )


if __name__ == "__main__":
    main()
