#Compute and clean missing values

import pandas as pd
import numpy as np
import config
from sklearn.preprocessing import StandardScaler

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

#fill NA stats with median for each position
def fill_missing_values(df,positions:list):
    processed = [] #list of processed variables with NA filled
    for i in positions:
        filled = df[df['athlete_position_abbreviation'] == i]
        filled = filled.replace([np.inf, -np.inf], pd.NA).fillna(filled[config.featureStatsWNBA].median())
        processed.append(filled)
    return processed

#Z-Score normalization
def normalize_features(df:list,cols):
    scaler = StandardScaler()
    normalized = []
    for i in df:
        scaled = pd.DataFrame(scaler.fit_transform(i[(cols)]), columns=cols, index=i.index)
        normalized.append(scaled)
    return normalized

#create a composite score
def composite_score(df,position,weightLongevity=1.5,weightRole=1,timeframe=False):
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