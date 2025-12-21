def merge_answers(groq_answer: str, gemini_result: dict) -> dict:
    """
    Merge strategy:
    - Default to Groq
    - Override ONLY if Gemini flags an error
    """

    if not gemini_result:
        return {
            "final_answer": groq_answer,
            "verification": "not_run",
        }

    if gemini_result.get("status") == "ok":
        return {
            "final_answer": groq_answer,
            "verification": "verified",
        }

    if gemini_result.get("status") == "corrected":
        return {
            "final_answer": gemini_result["fixed_answer"],
            "verification": "corrected",
            "original": groq_answer,
        }

    return {
        "final_answer": groq_answer,
        "verification": "unknown",
    }
