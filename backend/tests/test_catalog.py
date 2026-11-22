"""Game-setup catalogue: descriptions, piece guide and setup preview."""

from chakes.backend.catalog import piece_movement
from chakes.backend.models import GAME_TYPES


def _squares(name: str) -> dict[tuple[int, int], dict[str, bool]]:
    m = piece_movement(name)
    ox, oy = m["origin"]["x"], m["origin"]["y"]
    return {(s["x"] - ox, s["y"] - oy): s for s in m["squares"]}


# --- /api/game-types descriptions -------------------------------------------


def test_game_types_have_descriptions(client):
    body = client.get("/api/game-types").json()
    ids = {gt["id"] for gt in body["game_types"]}
    assert ids == set(GAME_TYPES)
    for gt in body["game_types"]:
        assert gt["name"]
        assert len(gt["description"]) > 20


def test_game_types_options(client):
    options = client.get("/api/game-types").json()["options"]
    assert "cooldown" in options
    assert "upside_down" in options


# --- piece_movement ----------------------------------------------------------


def test_knight_leaps_to_eight_squares():
    sq = _squares("Knight")
    assert set(sq) == {
        (1, 2),
        (2, 1),
        (-1, 2),
        (-2, 1),
        (1, -2),
        (2, -1),
        (-1, -2),
        (-2, -1),
    }
    assert all(s["move"] and s["capture"] and not s["ride"] for s in sq.values())


def test_rook_slides_orthogonally():
    sq = _squares("Rook")
    assert (4, 0) in sq and (0, -4) in sq and (1, 1) not in sq
    assert all(s["ride"] for s in sq.values())


def test_king_steps():
    sq = _squares("King")
    assert len(sq) == 8
    assert not any(s["ride"] for s in sq.values())


def test_pawn_move_and_capture_differ():
    sq = _squares("Pawn")
    assert set(sq) == {(0, 1), (0, 2), (1, 1), (-1, 1)}
    assert sq[(0, 1)]["move"] and not sq[(0, 1)]["capture"]
    assert sq[(0, 2)]["initial"] and sq[(0, 2)]["ride"]
    assert sq[(1, 1)]["capture"] and not sq[(1, 1)]["move"]


def test_berolina_pawn_is_mirrored_pawn():
    sq = _squares("Berolina Pawn")
    assert set(sq) == {(1, 1), (-1, 1), (2, 2), (-2, 2), (0, 1)}
    assert sq[(1, 1)]["move"] and not sq[(1, 1)]["capture"]
    assert sq[(2, 2)]["initial"]
    assert sq[(0, 1)]["capture"] and not sq[(0, 1)]["move"]


def test_anti_king_captures_friends_only():
    sq = _squares("Anti-King")
    assert len(sq) == 8
    assert all(s["move"] and s["friend"] and not s["capture"] for s in sq.values())


def test_archbishop_and_chancellor_compound():
    arch = _squares("Archbishop")
    assert (3, 3) in arch and (1, 2) in arch and (1, 0) not in arch
    assert arch[(3, 3)]["ride"] and not arch[(1, 2)]["ride"]
    chan = _squares("Chancellor")
    assert (0, 3) in chan and (2, 1) in chan and (1, 1) not in chan


def test_grasshopper_needs_hurdles():
    m = piece_movement("Grasshopper")
    assert len(m["hurdles"]) == 8
    sq = _squares("Grasshopper")
    assert (3, 0) in sq and sq[(3, 0)]["hop"]
    assert (1, 0) not in sq


# --- endpoints ---------------------------------------------------------------


def test_piece_guide_for_knighted(client):
    body = client.get("/api/piece-guide", params={"game_type": "knighted"}).json()
    names = {p["name"] for p in body["pieces"]}
    assert {"Archbishop", "Chancellor", "Pawn", "King"} <= names
    for p in body["pieces"]:
        assert p["movement"]["size"] == 9
        assert p["movement"]["squares"]
        assert p["default_cooldown"] >= 0


def test_piece_guide_default(client):
    names = [p["name"] for p in client.get("/api/piece-guide").json()["pieces"]]
    assert set(names) == {"Pawn", "Rook", "Knight", "Bishop", "Queen", "King"}


def test_piece_guide_matches_piece_defs(client):
    for gt in GAME_TYPES:
        guide = {
            p["name"]
            for p in client.get("/api/piece-guide", params={"game_type": gt}).json()[
                "pieces"
            ]
        }
        defs = {
            p["name"]
            for p in client.get("/api/piece-defs", params={"game_type": gt}).json()[
                "pieces"
            ]
        }
        assert guide == defs


def test_setup_preview_upside_down(client):
    normal = client.get("/api/setup-preview", params={"game_type": "orthodox"}).json()
    flipped = client.get(
        "/api/setup-preview", params={"game_type": "orthodox", "upside_down": True}
    ).json()
    assert normal["board"][0][4] == {"name": "King", "owner": "white"}
    assert flipped["board"][7][4] == {"name": "King", "owner": "white"}
    assert flipped["board"] == list(reversed(normal["board"]))
