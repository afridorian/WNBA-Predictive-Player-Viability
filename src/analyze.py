#create a composite score
def composite_score(df,position,weightLongevity=1.5,weightRole=1):
    #group stats by category and take average
    scoring = df[['field_goals_attempted','three_point_field_goals_attempted','free_throws_attempted','field_goals_made','three_point_field_goals_made','free_throws_made','points']].mean(axis=1)
    efficiency = df[['field_goal_percentage','free_throw_percentage','three_point_field_goal_percentage','true_shooting_percentage','points_per_minute','rebounds_per_minute','blocks_per_minute','steals_per_minute']].mean(axis=1)
    playmaking = df[['usage_percentage','assist_turnover_ratio','assists']].mean(axis=1)
    defense = df[['blocks','steals','rebounds']].mean(axis=1)
    longevity = df[['total_seasons','total_minutes','game_availability_percentage','total_games','games_started','minutes']].mean(axis=1)
    negativePerformance = df[['fouls','turnovers','turnovers_per_minute']].mean(axis=1)
    #assign different stats based on player position
    if position == 'guard':
        role = df[['steal_turnover_ratio','three_point_attempt_rate','drive_aggression','perimeter_shooting']].mean(axis=1)
    elif position == 'forward':
        role = df[['offensive_rebounds', 'defensive_rebounds', 'three_point_attempt_rate', 'drive_aggression','perimeter_shooting', 'rebound_share']].mean(axis=1)
    elif position == 'center':
        role = df[['offensive_rebounds','defensive_rebounds','rebound_share','free_throw_attempt_rate']].mean(axis=1)
    score = scoring + efficiency + playmaking + defense - negativePerformance + (longevity*weightLongevity) + (role*weightRole) #assign different weights based on feature tuning
    return score

