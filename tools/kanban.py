"""Minimal kanban board backed by a JSON file. Hermes Agent renders this same
board natively if kanban.board_path in hermes/config.yaml points here — this
module is what main.py uses to seed/advance cards between Hermes runs.
"""
import json
import os
import uuid
from datetime import datetime, timezone

BOARD_PATH = os.getenv("KANBAN_BOARD_PATH", "./kanban/board.json")
COLUMNS = ["Backlog", "In Progress", "Review", "Blocked", "Done"]


def _load() -> dict:
    if not os.path.exists(BOARD_PATH):
        board = {"columns": COLUMNS, "cards": []}
        _save(board)
        return board
    with open(BOARD_PATH) as f:
        return json.load(f)


def _save(board: dict) -> None:
    os.makedirs(os.path.dirname(BOARD_PATH), exist_ok=True)
    with open(BOARD_PATH, "w") as f:
        json.dump(board, f, indent=2)


def add_card(title: str, skill: str, column: str = "Backlog") -> dict:
    board = _load()
    card = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "skill": skill,
        "column": column,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    board["cards"].append(card)
    _save(board)
    return card


def next_card_for(skill: str) -> dict | None:
    board = _load()
    for card in board["cards"]:
        if card["skill"] == skill and card["column"] in ("Backlog", "In Progress"):
            return card
    return None


def move(card_id: str, to_column: str) -> None:
    assert to_column in COLUMNS
    board = _load()
    for card in board["cards"]:
        if card["id"] == card_id:
            card["column"] = to_column
    _save(board)


def has_open_cards() -> bool:
    board = _load()
    return any(c["column"] not in ("Done", "Blocked") for c in board["cards"])


def snapshot() -> str:
    board = _load()
    lines = []
    for col in COLUMNS:
        cards = [c for c in board["cards"] if c["column"] == col]
        lines.append(f"**{col}** ({len(cards)}): " + ", ".join(c["title"] for c in cards) or f"**{col}**: -")
    return "\n".join(lines)


def seed_default_board() -> None:
    """Call once to populate the board with the standard task set from the brief."""
    from tools.config_manager import load_config
    cfg = load_config()
    company = cfg.get("company_name", "Target Company")
    niche = cfg.get("niche", "Target Niche")

    defaults = [
        (f"Competitor research: top 5 {niche} competitors", "marketing_manager"),
        (f"Marketing strategy brief for {company}", "marketing_manager"),
        (f"Scrape Meta Ads Library — {niche}, last 30 days", "ads_manager"),
        ("Extract pain/hook/offer concepts from top ads", "ads_manager"),
        ("Draft ad script from best concept", "ads_manager"),
        (f"Find {niche} influencers", "influencer_outreach"),
        ("Draft personalized cold outreach per influencer", "influencer_outreach"),
        ("Repurpose provided YouTube sources into social content", "content_repurposer"),
    ]
    for title, skill in defaults:
        add_card(title, skill)
