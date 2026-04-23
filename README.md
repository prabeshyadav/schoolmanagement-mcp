# MCP Server — SchoolMS

A lightweight MCP (Model Context Protocol) server scaffold for the SchoolMS project. This repository contains the minimal server, helper modules, and prompts needed to run and develop the MCP server locally or inside Docker.

## Features

- Minimal MCP server entrypoints and helpers
- Docker and Docker Compose support for containerized runs
- `prompts/` folder with assistant instructions and examples

## Requirements

- Python 3.10+ (recommended)
- pip
- (Optional) Docker & Docker Compose for containerized runs

## Quick start

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the server locally (development):

```bash
python main.py
```

The server entrypoint is `main.py` which loads the MCP server module.

## Docker

Build and run using Docker:

```bash
docker build -t schoolms-mcp .
```

Or use Docker Compose:

```bash
docker-compose up --build
```

## Project structure

- [main.py](main.py) — Application entrypoint.
- [mcp_server.py](mcp_server.py) — MCP server implementation and orchestration.
- [brain.py](brain.py) — Project-specific logic/helpers.
- [requirements.txt](requirements.txt) — Python dependencies.
- [Dockerfile](Dockerfile) — Container image definition.
- [docker-compose.yml](docker-compose.yml) — Compose configuration for local stacks.
- [prompts/](prompts/) — Assistant instructions, examples, and prompt templates.

## Development

- Use the virtual environment for local development.
- Edit code in small commits and test by running `python main.py`.
- If you add dependencies, update `requirements.txt`:

```bash
pip freeze > requirements.txt
```

## Contributing

Contributions are welcome. Open issues for bugs or feature requests, and submit PRs for code changes.

## License

This repository does not include a license file. Add one if you plan to publish or share.

## Contact

If you have questions, open an issue or contact the maintainer.
