"""End-to-end tests through the HTTP API using TestClient."""


# ---------------------------------------------------------------------------
# Happy path: create → move → verify board changed
# ---------------------------------------------------------------------------

def test_happy_path_move_reflects_on_board(client):
    # Create lobby and game
    name = client.post("/api/lobby", params={"name": "e2e-lobby"}).json()["lobby"]
    game_id = client.post(f"/api/lobby/{name}/game").json()["game_id"]

    # Fetch legal moves for the e-pawn (r=1, c=4 → Pos(x=4, y=1))
    r = client.get(
        f"/api/lobby/{name}/game/{game_id}/legal-moves",
        params={"r": 1, "c": 4},
    )
    assert r.status_code == 200
    moves = r.json()["moves"]
    assert len(moves) > 0

    dst_x, dst_y = moves[0]

    # Apply the move
    r = client.post(
        f"/api/lobby/{name}/game/{game_id}/move",
        json={"src": {"x": 4, "y": 1}, "dst": {"x": dst_x, "y": dst_y}},
    )
    assert r.status_code == 200

    # Source square is now empty — legal-moves returns []
    r = client.get(
        f"/api/lobby/{name}/game/{game_id}/legal-moves",
        params={"r": 1, "c": 4},
    )
    assert r.json()["moves"] == []

    # Destination square is occupied — legal-moves returns non-empty
    r = client.get(
        f"/api/lobby/{name}/game/{game_id}/legal-moves",
        params={"r": dst_y, "c": dst_x},
    )
    assert len(r.json()["moves"]) > 0


# ---------------------------------------------------------------------------
# Illegal move: pawn jumping three squares → 400
# ---------------------------------------------------------------------------

def test_illegal_move_returns_400(client):
    name = client.post("/api/lobby", params={"name": "illegal-lobby"}).json()["lobby"]
    game_id = client.post(f"/api/lobby/{name}/game").json()["game_id"]

    r = client.post(
        f"/api/lobby/{name}/game/{game_id}/move",
        json={"src": {"x": 4, "y": 1}, "dst": {"x": 4, "y": 4}},
    )
    assert r.status_code == 400


def test_illegal_move_response_body(client):
    name = client.post("/api/lobby", params={"name": "illegal-body-lobby"}).json()["lobby"]
    game_id = client.post(f"/api/lobby/{name}/game").json()["game_id"]

    r = client.post(
        f"/api/lobby/{name}/game/{game_id}/move",
        json={"src": {"x": 4, "y": 1}, "dst": {"x": 4, "y": 4}},
    )
    assert r.json() == {"error": "Illegal move"}


# ---------------------------------------------------------------------------
# Lobby browser: player / spectator counts via WebSocket
# ---------------------------------------------------------------------------

def test_lobby_list_players_count_reflects_ws_connections(client, ws_connect):
    client.post("/api/lobby", params={"name": "ws-count-lobby"})
    ws_connect("ws-count-lobby", token="tok-a")
    ws_connect("ws-count-lobby", token="tok-b")
    r = client.get("/api/lobby")
    entry = next(e for e in r.json()["lobbies"] if e["name"] == "ws-count-lobby")
    assert entry["players"] == 2


def test_lobby_list_spectator_count_reflects_extra_ws(client, ws_connect):
    client.post("/api/lobby", params={"name": "ws-spec-lobby"})
    ws_connect("ws-spec-lobby", token="tok-a")
    ws_connect("ws-spec-lobby", token="tok-b")
    ws_connect("ws-spec-lobby")  # anonymous
    r = client.get("/api/lobby")
    entry = next(e for e in r.json()["lobbies"] if e["name"] == "ws-spec-lobby")
    assert entry["players"] == 2
    assert entry["spectators"] == 1


def test_lobby_list_disconnect_destroys_empty_lobby(client):
    client.post("/api/lobby", params={"name": "ws-destroy-lobby"})
    with client.websocket_connect("/api/lobby/ws-destroy-lobby/ws"):
        pass  # connect then immediately disconnect
    r = client.get("/api/lobby")
    names = [e["name"] for e in r.json()["lobbies"]]
    assert "ws-destroy-lobby" not in names


def test_lobby_list_state_transitions_waiting_to_in_progress(client):
    client.post("/api/lobby", params={"name": "state-lobby"})
    r = client.get("/api/lobby")
    entry = next(e for e in r.json()["lobbies"] if e["name"] == "state-lobby")
    assert entry["state"] == "waiting"

    client.post("/api/lobby/state-lobby/game")
    r = client.get("/api/lobby")
    entry = next(e for e in r.json()["lobbies"] if e["name"] == "state-lobby")
    assert entry["state"] == "in_progress"


def test_lobby_list_state_ended_after_checkmate(client):
    name = client.post("/api/lobby", params={"name": "mate-lobby"}).json()["lobby"]
    game_id = client.post(f"/api/lobby/{name}/game").json()["game_id"]

    # Fool's mate: f2→f3, e7→e5, g2→g4, d8→h4#
    for src, dst in [
        ({"x": 5, "y": 1}, {"x": 5, "y": 2}),
        ({"x": 4, "y": 6}, {"x": 4, "y": 4}),
        ({"x": 6, "y": 1}, {"x": 6, "y": 3}),
        ({"x": 3, "y": 7}, {"x": 7, "y": 3}),
    ]:
        client.post(f"/api/lobby/{name}/game/{game_id}/move", json={"src": src, "dst": dst})

    r = client.get("/api/lobby")
    entry = next(e for e in r.json()["lobbies"] if e["name"] == name)
    assert entry["state"] == "ended"
