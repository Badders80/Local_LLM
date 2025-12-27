import os
import json
import time
from pathlib import Path
from openai import OpenAI
from config import Config
from colorama import Fore, init

init(autoreset=True)


class Builder:
    def __init__(self):
        Config.validate()
        print(f"{Fore.CYAN}[System] Connecting to Local Forge (LM Studio)...")

        # Connect to LM Studio on Windows host (WSL2).
        host_ip = os.getenv("LM_STUDIO_HOST")
        if not host_ip:
            host_ip = "localhost"
            try:
                with open("/etc/resolv.conf", "r") as f:
                    for line in f:
                        if "nameserver" in line:
                            host_ip = line.split()[1]
                            break
            except Exception:
                pass

        base_url = os.getenv("LM_STUDIO_URL", f"http://{host_ip}:1234/v1")
        print(f"{Fore.CYAN}[System] LM Studio URL: {base_url}")

        self.client = OpenAI(
            base_url=base_url,
            api_key="lm-studio",
        )
        self.model = "local-model"

    def load_latest_plan(self) -> tuple[dict, Path]:
        """Finds the most recent plan in the artifacts folder."""
        files = list(Config.ARTIFACTS_DIR.glob("plan_*.json"))
        if not files:
            raise FileNotFoundError("No Architect plans found in artifacts/")

        latest_file = max(files, key=os.path.getctime)
        print(f"{Fore.CYAN}[Builder] Loaded plan: {latest_file.name}")

        with open(latest_file, "r") as f:
            return json.load(f), latest_file

    def execute_plan(
        self, plan_data: dict, plan_name: str | None = None, allow_network: bool = False
    ) -> Path:
        print(f"{Fore.CYAN}[Builder] Spooling up GPU...")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are The Builder. You are a highly skilled Python engineer. "
                    "Your ONLY goal is to execute the Architect's plan exactly. "
                    "Return ONLY the complete, runnable Python code. "
                    "Do not add markdown backticks (```) or explanation text. "
                    "Just the code. "
                    "If you generate plots, save them as PNG files in the current "
                    "directory instead of calling plt.show(). "
                    "Ensure the code runs as-is: define all variables, avoid "
                    "placeholder values that cause NameError, and keep network "
                    "calls inside functions where inputs are defined. "
                    "If network access is not allowed, do not call external APIs; "
                    "use mocked or local data instead. "
                    "When network access is allowed, validate HTTP responses and "
                    "handle API error payloads (e.g., missing keys); if required "
                    "fields are absent, print the response and exit cleanly."
                ),
            },
            {
                "role": "system",
                "content": (
                    f"Network access allowed: {allow_network}. "
                    "If false, avoid any outbound HTTP requests."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(plan_data, indent=2),
            },
        ]

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                stream=True,
            )

            print(f"{Fore.GREEN}[Builder] Generating Code:\n")

            full_code = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_code += content
            return self.save_artifact(full_code, plan_name)

        except Exception as e:
            print(f"\n{Fore.RED}[Builder] GPU Connection Failed: {e}")
            print(f"{Fore.YELLOW}Tip: Is LM Studio Server running on port 1234?")
            raise e

    def save_artifact(self, code: str, original_plan_name: str | None) -> Path:
        timestamp = None
        if original_plan_name and original_plan_name.startswith("plan_"):
            try:
                timestamp = int(original_plan_name.split("_")[1].split(".")[0])
            except (IndexError, ValueError):
                timestamp = None

        if timestamp is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"output_{timestamp}.py"
        save_path = Config.ARTIFACTS_DIR / filename

        with open(save_path, "w") as f:
            f.write(code)

        print(f"\n\n{Fore.CYAN}[System] Code saved to: {save_path}")
        return save_path


if __name__ == "__main__":
    builder = Builder()

    try:
        plan, plan_path = builder.load_latest_plan()
        _artifact_path = builder.execute_plan(plan, plan_path.name)
    except Exception as e:
        print(f"{Fore.RED}[System] Build Failed.")
