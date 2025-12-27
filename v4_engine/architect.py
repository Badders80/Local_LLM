import json
import time
import signal
import sys
from typing import List
from pydantic import BaseModel, Field
from groq import Groq
from config import Config
from colorama import Fore, init

init(autoreset=True)


def signal_handler(sig, frame):
    print(f"\n{Fore.RED}[System] Interrupt received. Shutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class Step(BaseModel):
    id: int
    action: str = Field(..., description="Action verb")
    details: str = Field(..., description="Precise instructions")


class ExecutionPlan(BaseModel):
    analysis: str
    steps: List[Step]
    estimated_complexity: str
    safety_flag: bool


class Architect:
    def __init__(self):
        Config.validate()
        print(f"{Fore.CYAN}[System] Hardware verified. Root: {Config.PROJECT_ROOT}")
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def create_plan(self, user_query: str) -> dict:
        print(f"{Fore.CYAN}[Architect] Analyzing request via Groq Cloud...")
        start_time = time.time()

        try:
            # Added clearer schema instructions to the prompt.
            schema_desc = (
                "JSON Schema required:\n"
                "{\n"
                '  "analysis": "string",\n'
                '  "steps": [{"id": int, "action": "string", "details": "string"}],\n'
                '  "estimated_complexity": "string",\n'
                '  "safety_flag": boolean\n'
                "}"
            )

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are The Architect. You plan software execution steps. "
                            "Output a valid, flat JSON object matching the schema. "
                            "Do NOT wrap the output in a key like 'execution_plan'.\n\n"
                            f"{schema_desc}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_query,
                    },
                ],
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            raw_content = chat_completion.choices[0].message.content
            data = json.loads(raw_content)

            # If the model wraps the output in a known key, unwrap it.
            if "execution_plan" in data:
                data = data["execution_plan"]
            elif "plan" in data:
                data = data["plan"]
            elif "response" in data:
                data = data["response"]

            plan = ExecutionPlan(**data)
            print(f"{Fore.GREEN}[Architect] Plan created in {time.time() - start_time:.2f}s")
            return plan.model_dump(mode="json")

        except Exception as e:
            print(f"{Fore.RED}[Architect] Planning Failed: {e}")
            print(f"{Fore.RED}Raw Output was: {raw_content}")
            raise e


if __name__ == "__main__":
    architect = Architect()
    try:
        plan_data = architect.create_plan("Draft a Python script to fetch weather data.")
        plan = ExecutionPlan(**plan_data)

        print(f"\n{Fore.YELLOW}=== ARCHITECT'S PLAN ===")
        for step in plan.steps:
            print(f"  {step.id}. [{step.action}] {step.details}")

        save_path = Config.ARTIFACTS_DIR / f"plan_{int(time.time())}.json"
        with open(save_path, "w") as f:
            f.write(json.dumps(plan_data, indent=2))

        print(f"\n{Fore.CYAN}[System] Plan persisted to: {save_path}")

    except Exception as e:
        print(f"{Fore.RED}[System] Critical Failure: {e}")
