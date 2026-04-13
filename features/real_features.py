import pandas as pd

def calculate_form(df, team, is_home=True):

    if is_home:
        team_matches = df[df["home_team"] == team]
        goals_for = team_matches["home_goals"]
        goals_against = team_matches["away_goals"]
    else:
        team_matches = df[df["away_team"] == team]
        goals_for = team_matches["away_goals"]
        goals_against = team_matches["home_goals"]

    last5 = team_matches.tail(5)

    if len(last5) == 0:
        return 0.0

    return (goals_for.tail(5).mean() - goals_against.tail(5).mean())


def build_real_features(df, home_team, away_team):

    home_form = calculate_form(df, home_team, True)
    away_form = calculate_form(df, away_team, False)

    momentum = home_form - away_form
    market_edge = momentum * 0.2

    return [
        float(home_form),
        float(away_form),
        float(market_edge)
    ]
