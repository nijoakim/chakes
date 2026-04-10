
# Package structure

This package lives in a monorepo, but is self-contained.
The following structure allows `import chakes.engine` from the backend.

```
chakes/                  # Monorepo
    backend/
    engine/              # Root for this package
        pyproject.toml
        chakes/          # PEP420 implicit namespace (no __init__.py)
            engine/      # The "actual" package
    frontend/
```
