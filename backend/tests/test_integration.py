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
