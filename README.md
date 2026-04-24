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


- Dragloggar enkelt tillgängliga (motor som exponeras i klient).
- Ny match (med nytt spel-id) med samma spelare
- Visa text när man vinner.
- Visa legal moves (med svag grön).
- backend: borde ej bli 500 vid illeagal move
- Lägg till gå med höger (utför giltigt drag och avmarkerar) _och_ vänster klick på ogiltiga drag avmarkerar, esc avmarkerar.
- Läs default pjäser från motor och presentera klienten (e.g. coolsdowns ska komma från GameState)
- När man skapar så bestämmer man cooldowns
