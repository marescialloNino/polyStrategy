#!/usr/bin/env python3
import asyncio
import csv
import re
import json
from datetime import datetime

from core.clob_client import PolymarketClient
from core.gamma_client import GammaMarketsClient

GAME_SLUG_RE = re.compile(r"^nba-[^-]+-[^-]+-\d{4}-\d{2}-\d{2}$", re.IGNORECASE)

async def main():
    clob = PolymarketClient()
    gamma = GammaMarketsClient()

    markets     = gamma.get_markets(
        closed=False,
        liquidity_num_min=30_000.0,
        volume_num_min=5_000.0,
        start_date_min="2025-04-20",
        tag_id=1,
    )
    nba_markets = clob.filter_markets_by_slug_keyword(markets, keyword="nba")
    games       = [m for m in nba_markets if GAME_SLUG_RE.match(m.get("slug", ""))]

    if not games:
        print("No NBA game markets found.")
        return

    with open("../poly_nba_odds.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # the eight required headers:
        writer.writerow([
            "timestamp",
            "home_team",
            "away_team",
            "start_time",
            "home_win_odds",
            "draw_odds",
            "away_win_odds",
            "event_name",
        ])

        for m in games:
            # parse the two team names from the outcomes JSON
            outcomes = json.loads(m.get("outcomes", "[]"))
            home_team = outcomes[0] if len(outcomes) > 0 else ""
            away_team = outcomes[1] if len(outcomes) > 1 else ""

            # midpoint prices from the market object
            outcome_prices = json.loads(m.get("outcomePrices", "[]"))
            home_win_odds = outcome_prices[0] if len(outcome_prices) > 0 else ""
            away_win_odds = outcome_prices[1] if len(outcome_prices) > 1 else ""

            # Polymarket has no draw, so leave blank
            draw_odds = ""

            # event name can be the question text
            event_name = m.get("question", "")

            # start_time: use the ISO timestamp field if available
            start_time = m.get("startTime", m.get("startDateIso", ""))

            # timestamp = time of fetch
            timestamp = datetime.now().isoformat()

            writer.writerow([
                timestamp,
                home_team,
                away_team,
                start_time,
                home_win_odds,
                draw_odds,
                away_win_odds,
                event_name,
            ])

    print(f"Wrote {len(games)} rows with normalized headers to nba_markets.csv")

if __name__ == "__main__":
    asyncio.run(main())
