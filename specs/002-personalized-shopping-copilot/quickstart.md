# Planning Validation Quickstart

Phase 7 has no application implementation. From repository root:

```bash
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks
python3 -c "import yaml; yaml.safe_load(open('specs/002-personalized-shopping-copilot/contracts/openapi.yaml'))"
rg '\[NEEDS CLARIFICATION|\[FEATURE|TXXX|REMOVE IF UNUSED' specs/002-personalized-shopping-copilot
git diff --check
```

Future implementation starts with Milestone A tests and offline fixtures. Do not supply a real key or activate OpenAI from Iran. Compose remains mock/offline by default.
