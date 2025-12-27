import subprocess
import os
from pathlib import Path
from config import Config
from colorama import Fore, init

init(autoreset=True)


class Executor:
    def __init__(self):
        Config.validate()
        self.image = "v4-sandbox"  # Prebuilt sandbox image with common libs

    def run_artifact(
        self, script_filename: str, timeout: int = 30, allow_network: bool = False
    ):
        # Full path to the generated script in your artifacts folder
        script_path = Config.ARTIFACTS_DIR / script_filename

        if not script_path.exists():
            print(f"{Fore.RED}[Executor] Script not found: {script_filename}")
            return

        print(f"{Fore.YELLOW}[Executor] Launching Sandbox for {script_filename}...")

        # Docker Command Construction
        # --rm: Destroy container after execution
        # -v: Mount ONLY the artifacts folder to /app in the container
        # --network none: No internet access for the script
        # -w: Set working directory inside the container
        cmd = ["docker", "run", "--rm"]
        if allow_network:
            cmd += ["--network", "host"]
        else:
            cmd += ["--network", "none"]
        cmd += [
            "-v",
            f"{Config.ARTIFACTS_DIR}:/app",
            "-w",
            "/app",
            self.image,
            "python",
            script_filename,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            print(f"{Fore.GREEN}--- SANDBOX OUTPUT ---")
            print(result.stdout)

            if result.stderr:
                print(f"{Fore.RED}--- SANDBOX ERRORS ---")
                print(result.stderr)

        except subprocess.TimeoutExpired:
            print(
                f"{Fore.RED}[Executor] CRITICAL: Script timed out (Infinite loop protection)."
            )
        except Exception as e:
            print(f"{Fore.RED}[Executor] Sandbox Failed: {e}")


if __name__ == "__main__":
    # Test with the last generated file (example: output_1766729250.py)
    # You can find the filename in your artifacts folder
    import glob

    files = glob.glob(str(Config.ARTIFACTS_DIR / "output_*.py"))
    if files:
        latest_output = os.path.basename(max(files, key=os.path.getctime))
        exec = Executor()
        exec.run_artifact(latest_output)
    else:
        print("No output scripts found to execute.")
