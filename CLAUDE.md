# CLAUDE.md - Local_LLM

## What this repo is and what it solves
Local_LLM contains the local LLM integration for Evolution Stables. It solves the problem of running large language models locally by providing a unified interface for Ollama and LlamaCPP.

## Full Stack
### What IS used:
- **Python 3.12** for integration
- **Ollama** for running LLMs
- **LlamaCPP** for quantized models
- **Docker** for containerization
- **FastAPI** for API endpoints

### What IS NOT used:
- **OpenAI**: Not used (Local LLMs preferred)
- **Google Generative AI**: Not used (Local LLMs preferred)

## Hard Coding Rules

1. **No empty placeholder files** - Implement or don't create the file
2. **Models must be quantized** - Respect RTX 3060 VRAM limits
3. **Performance must be optimized** - Use --lowvram mode if needed
4. **Error handling must be robust** - Handle LLM failures gracefully

## Project Structure
```
Local_LLM/
├── src/                  # Source code
│   ├── llm_integration.py  # Main LLM integration
│   └── models/            # Quantized LLM models
├── config/               # Configuration files
├── tests/                # Test files
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker configuration
└── README.md             # Documentation
```

## Key Features
1. **Local LLM Integration**: Runs LLMs locally using Ollama or LlamaCPP
2. **Model Management**: Downloads and manages quantized models
3. **API Endpoints**: Provides LLM access via FastAPI
4. **Error Handling**: Handles LLM failures and retries

## Environment Variables
Required environment variables in `.env`:
```
OLLAMA_BASE_URL=
LLAMA_CPP_PATH=
```

## WSL2 Paths
- **Project Path**: `/home/evo/projects/Local_LLM/`
- **Windows Path**: `C:\Users\Evo\projects\Local_LLM\`
- **Dev Server Port**: 8002 (default)

## Current Phase and Next Build Target
- **Current Phase**: Scaffolded
- **Next Build Target**: Implement real LLM integration

## Commands
- **Run Server**: `python src/llm_integration.py` (runs on port 8002)
- **Install Dependencies**: `pip install -r requirements.txt`

## Source of Truth
**All development standards are defined in 00_DNA**:
- **Build Philosophy**: `/home/evo/00_DNA/build-philosophy/Master_Config_2026.md`
- **System Prompts**: `/home/evo/00_DNA/system-prompts/PROMPT_LIBRARY.md`
- **Brand Voice**: `/home/evo/00_DNA/brand-identity/BRAND_VOICE.md`
- **Workflows**: `/home/evo/00_DNA/workflows/`

**Key Files to Reference**:
1. `/home/evo/00_DNA/AGENTS.core.md` - Universal agent rules
2. `/home/evo/00_DNA/build-philosophy/Master_Config_2026.md` - Hardware and architecture specs
3. `/home/evo/00_DNA/brand-identity/MESSAGING_CHEAT_SHEET.md` - Brand voice guidelines
