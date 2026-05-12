from chakes.backend.messages import GameStateMessage
from chakes.backend.models import ActiveGame, GameDef


# ---------------------------------------------------------------------------
# GET /api/game-types
# ---------------------------------------------------------------------------

def test_game_types_returns_200(client):
    r = client.get("/api/game-types")
    assert r.status_code == 200


def test_game_types_contains_orthodox(client):
    r = client.get("/api/game-types")
    ids = [gt["id"] for gt in r.json()["game_types"]]
    assert "orthodox" in ids


# ---------------------------------------------------------------------------
# GET /api/piece-defs
# ---------------------------------------------------------------------------

def test_piece_defs_default_returns_200(client):
    r = client.get("/api/piece-defs")
    assert r.status_code == 200


def test_piece_defs_knighted_returns_200(client):
    r = client.get("/api/piece-defs", params={"game_type": "knighted"})
    assert r.status_code == 200


def test_piece_defs_default_and_knighted_differ(client):
    default = client.get("/api/piece-defs").json()
    knighted = client.get("/api/piece-defs", params={"game_type": "knighted"}).json()
    assert default["pieces"] != knighted["pieces"]


# ---------------------------------------------------------------------------
# POST /api/lobby
# ---------------------------------------------------------------------------

def test_lobby_create_no_body_returns_200(client):
    r = client.post("/api/lobby")
    assert r.status_code == 200


def test_lobby_create_no_body_returns_lobby_name(client):
    r = client.post("/api/lobby")
    assert "lobby" in r.json()


def test_lobby_create_with_name_returns_that_name(client):
    r = client.post("/api/lobby", params={"name": "my-lobby"})
    assert r.json()["lobby"] == "my-lobby"


# ---------------------------------------------------------------------------
# GET /api/lobby/{name}
# ---------------------------------------------------------------------------

def test_lobby_get_returns_expected_keys(client):
    client.post("/api/lobby", params={"name": "alpha"})
    r = client.get("/api/lobby/alpha")
    assert r.status_code == 200
    data = r.json()
    assert "name" in data
    assert "game_id" in data


def test_lobby_get_name_matches(client):
    client.post("/api/lobby", params={"name": "beta"})
    r = client.get("/api/lobby/beta")
    assert r.json()["name"] == "beta"


def test_lobby_get_game_id_none_before_game_created(client):
    client.post("/api/lobby", params={"name": "gamma"})
    r = client.get("/api/lobby/gamma")
    assert r.json()["game_id"] is None


# ---------------------------------------------------------------------------
# GameStateMessage shape
# ---------------------------------------------------------------------------

def test_game_state_message_board_dimensions():
    game = ActiveGame(GameDef())
    msg = GameStateMessage.from_active_game(game)
    assert len(msg.board) == game.state.size_y
    assert all(len(row) == game.state.size_x for row in msg.board)


def test_game_state_message_empty_squares_are_none():
    game = ActiveGame(GameDef())
    msg = GameStateMessage.from_active_game(game)
    # rows 2-5 are empty on a fresh orthodox board
    for r in range(2, 6):
        assert all(sq is None for sq in msg.board[r])


def test_game_state_message_populated_squares_have_name_and_owner():
    game = ActiveGame(GameDef())
    msg = GameStateMessage.from_active_game(game)
    for row in msg.board:
        for sq in row:
            if sq is not None:
                assert "name" in sq
                assert "owner" in sq


def test_game_state_message_no_winner_omits_winner_key():
    game = ActiveGame(GameDef())
    msg = GameStateMessage.from_active_game(game)
    dumped = msg.model_dump(exclude_none=True)
    assert "winner" not in dumped


# ---------------------------------------------------------------------------
# GET /api/server
# ---------------------------------------------------------------------------

def test_server_endpoint_returns_200(client):
    r = client.get("/api/server")
    assert r.status_code == 200


def test_server_endpoint_returns_name_key(client):
    r = client.get("/api/server")
    assert "name" in r.json()


def test_server_endpoint_name_matches_module_constant(client):
    from chakes.backend.server_identity import SERVER_NAME
    r = client.get("/api/server")
    assert r.json()["name"] == SERVER_NAME


# ---------------------------------------------------------------------------
# GET /api/lobby (list)
# ---------------------------------------------------------------------------

def test_lobby_list_returns_200(client):
    r = client.get("/api/lobby")
    assert r.status_code == 200


def test_lobby_list_returns_server_name_at_top_level(client):
    r = client.get("/api/lobby")
    data = r.json()
    assert "server_name" in data
    assert data["server_name"]


def test_lobby_list_empty_when_no_lobbies(client):
    r = client.get("/api/lobby")
    assert r.json()["lobbies"] == []


def test_lobby_list_includes_created_lobby(client):
    client.post("/api/lobby", params={"name": "list-foo"})
    r = client.get("/api/lobby")
    names = [e["name"] for e in r.json()["lobbies"]]
    assert "list-foo" in names


def test_lobby_list_entry_has_required_keys(client):
    client.post("/api/lobby", params={"name": "list-keys"})
    r = client.get("/api/lobby")
    entry = r.json()["lobbies"][0]
    assert {"name", "server_name", "state", "players", "spectators", "settings"} <= entry.keys()


def test_lobby_list_entry_state_is_waiting_before_game_create(client):
    client.post("/api/lobby", params={"name": "list-waiting"})
    r = client.get("/api/lobby")
    entry = next(e for e in r.json()["lobbies"] if e["name"] == "list-waiting")
    assert entry["state"] == "waiting"


def test_lobby_list_entry_state_is_in_progress_after_game_create(client, lobby_with_game):
    name, _ = lobby_with_game
    r = client.get("/api/lobby")
    entry = next(e for e in r.json()["lobbies"] if e["name"] == name)
    assert entry["state"] == "in_progress"


def test_lobby_list_entry_settings_null_when_waiting(client):
    client.post("/api/lobby", params={"name": "list-null-settings"})
    r = client.get("/api/lobby")
    entry = next(e for e in r.json()["lobbies"] if e["name"] == "list-null-settings")
    assert entry["settings"] is None


def test_lobby_list_entry_settings_populated_when_in_progress(client, lobby_with_game):
    name, _ = lobby_with_game
    r = client.get("/api/lobby")
    entry = next(e for e in r.json()["lobbies"] if e["name"] == name)
    assert entry["settings"]["game_type_id"] == "orthodox"


def test_lobby_list_entry_server_name_matches_top_level(client):
    client.post("/api/lobby", params={"name": "list-srv-name"})
    r = client.get("/api/lobby")
    data = r.json()
    assert all(e["server_name"] == data["server_name"] for e in data["lobbies"])
