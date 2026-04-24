# Chakes: Real-time chess for the masses.

## Set up dev environment

Make sure you have `uv` installed (`python -m pip install uv`). Then

```bash
uv sync --all-packages
make run-backend
```

Frontend requires node 24. Install with e.g. `sudo snap install node --classic --channel 24` (ubuntu).

Use the `.env.example` file to configure your own local setup (copy to `.env`).
Configurable environment variables:
- BACKEND_PORT: the port the backend uses to serve content
