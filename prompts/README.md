Prompts folder

Purpose:
- Store canonical system and assistant instruction templates and a few-shot set for the SchoolMS MCP.

Files:
- `system.txt` — authoritative system message for the model.
- `assistant_instructions.txt` — behavior rules and output schema.
- `examples.md` — few-shot examples to teach desired behavior.

How to use in `main.py`:
- If `prompts/system.txt` exists, `main.py` will load it and inject as the system message.
- You can update these files to iterate on model behavior without changing code.

Next steps:
- Optionally add `tests/prompts_test.py` to validate outputs against examples.
