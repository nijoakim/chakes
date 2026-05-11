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

## Board coordinate system

The board displays rank (row) and file (column) labels around the border, following standard chess notation conventions extended for arbitrary board sizes.

**Files (columns):** labeled left-to-right from the white player's perspective using the following alphabet sequence:

| Range     | Labels          | Count |
|-----------|-----------------|-------|
| 1–26      | `a`–`z`         | 26    |
| 27–52     | `A`–`Z`         | 26    |
| 53–76     | `α`–`ω` (Greek) | 24    |

This covers boards up to 76 columns wide (well beyond the 64-column maximum).

**Ranks (rows):** labeled 1–N, with rank 1 at white's back rank (bottom of the board from white's perspective).

**Orientation:** labels always reflect the true board coordinate regardless of which player's perspective is shown. From black's perspective the board is flipped — rank 1 appears at the top and files are mirrored — but the label values remain consistent with the underlying coordinate system.
