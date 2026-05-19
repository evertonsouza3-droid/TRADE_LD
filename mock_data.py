import random
from datetime import datetime, timedelta

# List of realistic matchups with their respective leagues
MATCH_TEMPLATES = [
    # Brasileirão Série A
    {"home": "Flamengo", "away": "Palmeiras", "competition": "Brasileirão Série A", "avg_goals": 2.6},
    {"home": "São Paulo", "away": "Corinthians", "competition": "Brasileirão Série A", "avg_goals": 2.3},
    {"home": "Atlético Mineiro", "away": "Cruzeiro", "competition": "Brasileirão Série A", "avg_goals": 2.4},
    {"home": "Botafogo", "away": "Fluminense", "competition": "Brasileirão Série A", "avg_goals": 2.7},
    {"home": "Grêmio", "away": "Internacional", "competition": "Brasileirão Série A", "avg_goals": 2.2},
    {"home": "Athletico-PR", "away": "Bahia", "competition": "Brasileirão Série A", "avg_goals": 2.5},
    
    # Premier League
    {"home": "Arsenal", "away": "Chelsea", "competition": "Premier League", "avg_goals": 3.1},
    {"home": "Liverpool", "away": "Manchester United", "competition": "Premier League", "avg_goals": 3.4},
    {"home": "Manchester City", "away": "Tottenham", "competition": "Premier League", "avg_goals": 3.6},
    {"home": "Newcastle", "away": "Aston Villa", "competition": "Premier League", "avg_goals": 2.9},
    
    # La Liga
    {"home": "Real Madrid", "away": "Barcelona", "competition": "La Liga", "avg_goals": 3.2},
    {"home": "Atlético Madrid", "away": "Real Sociedad", "competition": "La Liga", "avg_goals": 2.4},
    {"home": "Sevilla", "away": "Real Betis", "competition": "La Liga", "avg_goals": 2.3},
    
    # Champions League
    {"home": "Bayern Munich", "away": "Paris Saint-Germain", "competition": "UEFA Champions League", "avg_goals": 3.3},
    {"home": "Inter Milan", "away": "Juventus", "competition": "UEFA Champions League", "avg_goals": 2.5},
    {"home": "Borussia Dortmund", "away": "AC Milan", "competition": "UEFA Champions League", "avg_goals": 2.8}
]

def generate_mock_data():
    """
    Generates dynamic mock datasets that match the exact JSON structure of:
    1. football-data.org (/v4/matches)
    2. the-odds-api.com (/v4/sports/soccer/odds)
    
    This ensures the parsing logic in app.py works seamlessly in both Real API and Simulation modes.
    """
    matches_payload = {"matches": []}
    odds_payload = []
    
    # Current time to generate realistic upcoming UTC times
    base_time = datetime.utcnow()
    
    # Shuffle templates to make it look dynamic on refresh
    shuffled_templates = list(MATCH_TEMPLATES)
    random.shuffle(shuffled_templates)
    
    for i, match in enumerate(shuffled_templates):
        # 1. Structure for Football-Data API
        # Matches are scheduled for today, spaced by 1 hour increments
        match_time = base_time + timedelta(hours=1 + i)
        utc_date_str = match_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        match_entry = {
            "id": 1000 + i,
            "utcDate": utc_date_str,
            "status": "SCHEDULED",
            "competition": {
                "name": match["competition"]
            },
            "homeTeam": {
                "name": match["home"]
            },
            "awayTeam": {
                "name": match["away"]
            }
        }
        matches_payload["matches"].append(match_entry)
        
        # 2. Structure for The Odds API (Draw H2H)
        # We simulate market odds. For Lay the Draw (LD), draw odds typically range from 2.9 to 5.0.
        # We make some draws EV+ (odd < 3.70 when model avg is 2.8) and some EV- (odd > 3.70)
        draw_odd = round(random.uniform(2.8, 4.8), 2)
        
        odds_entry = {
            "id": f"odds_{i}",
            "sport_key": "soccer",
            "sport_title": "Soccer",
            "commence_time": utc_date_str,
            "home_team": match["home"],
            "away_team": match["away"],
            "bookmakers": [
                {
                    "key": "bet365",
                    "title": "Bet365",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": match["home"], "price": round(random.uniform(1.5, 4.0), 2)},
                                {"name": match["away"], "price": round(random.uniform(1.8, 5.0), 2)},
                                {"name": "Draw", "price": draw_odd}
                            ]
                        }
                    ]
                }
            ]
        }
        odds_payload.append(odds_entry)
        
    return matches_payload, odds_payload
