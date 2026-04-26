#Compute and clean missing values

import pandas as pd

#get get team totals
def compute_team_totals(df):
    df['total_available_games'] = df.groupby(['season', 'team_display_name'])['game_id'].transform('nunique') #get number of games that each team played each season
    games = df.groupby(['game_id','team_display_name'])[['minutes','field_goals_made','field_goals_attempted','three_point_field_goals_made','three_point_field_goals_attempted','free_throws_made','free_throws_attempted','offensive_rebounds','defensive_rebounds','rebounds','assists','steals','blocks','turnovers','fouls','points']].sum()
    games['team_possessions'] = round(games['field_goals_attempted'] + .44 * games['free_throws_attempted'] - games['offensive_rebounds'] + games['turnovers'],2) #calculate number of possessions a team had throughout each game
    games['team_metric'] = round((games['field_goals_attempted'] + .44 * games['free_throws_attempted'] + games['turnovers']),3) #calculate team performance metric
    games['total_available_games'] = df.groupby(['game_id', 'team_display_name'])['total_available_games'].first() #add total available games each team played each season to the new df
    games = games.rename(columns={'rebounds':'team_rebounds','minutes':'team_minutes'}).reset_index() #rename columns for clarity
    return games #return the df to store as a variable for further processing

#per game stats
def compute_true_shooting_pct(df,pointsCol,fgAttemptCol,ftAttemptCol,decimals=3):
    return (df[pointsCol]/(2*(df[fgAttemptCol]+.44*df[ftAttemptCol]))).round(decimals)

def compute_ratios(df,numeratorCol,denominatorCol,decimals=3):
    return (df[numeratorCol]/df[denominatorCol].replace(0,pd.NA)).round(decimals)

#find players with missing positions and correct multiple position entries
def get_missing_positions(df1,df2,df3=None):
    df1['athlete_position_abbreviation'] = df1['athlete_position_abbreviation'].replace('NA', pd.NA) #replace string NA with pandas NA
    positions1 = (df2[['athlete_display_name', 'athlete_position_abbreviation']].dropna().drop_duplicates(subset='athlete_display_name').set_index('athlete_display_name')['athlete_position_abbreviation']) #create list of player positions based on first appearance of athlete display name
    df1['athlete_position_abbreviation'] = df1['athlete_position_abbreviation'].fillna(df1['athlete_display_name'].map(positions1)) #map the list of unique positions to the original df for players who have missing positions
    if df3 is not None: #optional argument if there are multiple sources that contain player positions
        positions2 = (df3[['athlete_display_name', 'athlete_position_abbreviation']].dropna().drop_duplicates(subset='athlete_display_name').set_index('athlete_display_name')['athlete_position_abbreviation'])  #create list of player positions based on first appearance of athlete display name
        df1['athlete_position_abbreviation'] = df1['athlete_position_abbreviation'].fillna(df1['athlete_display_name'].map(positions2)) #map the list of unique positions to the original df for players who have missing positions
        positionRank = {'G': 1, 'C': 2, 'F': 3} #set preference order for players who have more than one position based on different seasons
        positionList = df1[['athlete_display_name', 'athlete_position_abbreviation']].dropna(subset=['athlete_position_abbreviation']).drop_duplicates().assign(priority=df1['athlete_position_abbreviation'].map(positionRank)).sort_values('priority').drop_duplicates(subset='athlete_display_name').set_index('athlete_display_name')['athlete_position_abbreviation']
        df1['athlete_position_abbreviation'] = df1['athlete_display_name'].map(positionList) #map the list of unique positions to the original df for players who have missing positions
    df1['athlete_position_abbreviation'] = df1['athlete_position_abbreviation'].replace('G-F', 'G') #normalize positions with multiple positions in one col
    df1['athlete_position_abbreviation'] = df1['athlete_position_abbreviation'].replace('F-C', 'C') #normalize positions with multiple positions in one col
    return df1

