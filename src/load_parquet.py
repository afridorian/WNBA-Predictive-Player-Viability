import pandas as pd
import requests
import os

#PARQUET DATA PRE-PROCESSING FUNCTIONS
#download files from git repo
def download_git(url,filePath):
    data = requests.get(url).json()
    for i in data['assets']:
        if '.parquet' in i['name']:
            name = i['name']
            downloadURL = requests.get(i['browser_download_url'])
            downloadPath = os.path.join(filePath, name)
            with open(downloadPath, 'wb') as output:
                output.write(downloadURL.content)
    print(f"Files downloaded to {filePath}.")

#DATA CLEANING FUNCTIONS
#create one parquet from multiple files in a directory
def concat_files(files, filePath, outputPath): #take original filePath, range of dates, output file name
    #normalize column names for input file
    columnMap = {"min": "minutes",
                 "fg": "field_goals_attempted",
                 "fg3": "three_point_field_goals_attempted",
                 "ft": "free_throws_attempted",
                 "oreb": "offensive_rebounds",
                 "dreb": "defensive_rebounds",
                 "reb": "rebounds",
                 "ast": "assists",
                 "stl": "steals",
                 "blk": "blocks",
                 "to": "turnovers",
                 "pf": "fouls",
                 "pts": "points",
                 "starter": "games_started"
                 }

    url = [f'{filePath}/{i}' for i in files] #get full path for each file
    output = [pd.read_parquet(i).rename(columns=columnMap) for i in url] #normalize column names each file
    concat = pd.concat(output, join='outer', ignore_index=True) #ignore index so the duplicates don't overwrite
    concat.to_parquet(outputPath)
    print(f'{files} successfully joined.')
    return concat #output df

#clean up parquet dataSet to account for nan, mixed types, missing values
def normalize(filePath):

    parquetFile = pd.read_parquet(filePath)
    #add the collegeAthPg headers here for each data set
    headers = {"int": ['game_id', 'season', 'season_type', 'athlete_id', 'team_id','minutes','field_goals_made',
                       'field_goals_attempted', 'three_point_field_goals_made', 'three_point_field_goals_attempted',
                       'free_throws_made', 'free_throws_attempted', 'offensive_rebounds', 'defensive_rebounds',
                       'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'fouls', 'plus_minus', 'points',
                       'athlete_jersey', 'team_score', 'opponent_team_id', 'opponent_team_score','weight','height','totalWNBASeasons',
                       'NCAA_athlete_id','totalNCAASeasons','games_played','two_point_field_goals_made','two_point_field_goals_attempted',
                       'games_started','draft'],
               "float": ['field_goal_percentage','free_throw_percentage','three_point_field_goal_percentage','true_shooting_percentage','effective_field_goal_percentage',
                         'three_point_attempt_rate','free_throw_attempt_rate','offensive_rebound_percentage',
                         'defensive_rebound_percentage','total_rebound_percentage','assist_percentage','steal_percentage',
                         'block_percentage','turnover_percentage','usage_percentage','offensive_rating','defensive_rating',
                         'avg_min','avg_fg_made','avg_fg_attempt','avg_fg_pct','avg_3p_fg_made','avg_3p_fg_attempt','avg_3p_fg_pct',
                         'avg_2p_fg_made','avg_2p_fg_attempt','avg_2p_fg_pct','avg_effective_fg_pct','avg_ft_made','avg_ft_attempt',
                         'avg_ft_pct','avg_off_reb','avg_def_reb','avg_rebounds','avg_assists','avg_steals','avg_blocks',
                         'avg_turnovers','avg_fouls','avg_points','steal_foul_ratio','steal_turnover_ratio','two_point_field_goal_percentage'],
               "dt": ['game_date_time','DOB'],
               "date": ['game_date'],
               "bool": ['games_started','ejected','did_not_play','active','team_winner','NCAAStats'],
               "str": ['athlete_display_name', 'team_name', 'team_location', 'team_short_display_name',
                       'athlete_short_name', 'athlete_position_name', 'athlete_position_abbreviation',
                       'team_display_name', 'team_uid', 'team_slug', 'team_logo', 'team_abbreviation', 'team_color',
                       'team_alternate_color', 'home_away', 'opponent_team_name', 'opponent_team_location',
                       'opponent_team_display_name', 'opponent_team_abbreviation', 'opponent_team_logo',
                       'opponent_team_color', 'opponent_team_alternate_color', 'athlete_headshot_href', 'reason','position',
                       'status','class']
               }

    #get a list of values, apply conversion to all values of each corresponding column in the list
    for i in headers:
        inc = [val for val in headers[i] if val in parquetFile.columns] #list of headers to include, avoid keyerror
        if inc: #make sure inc isn't empty
            if i == "int":
                parquetFile[inc] = parquetFile[inc].apply(pd.to_numeric, errors='coerce').astype('Int64')  # int normalization
            if i == "float":
                parquetFile[inc] = parquetFile[inc].apply(pd.to_numeric, errors='coerce')  # float normalization
            if i == "dt":
                parquetFile[inc] = parquetFile[inc].apply(pd.to_datetime, errors='coerce')  # datetime normalization
            if i == "date":
                for v in inc:
                    inc = str(v)
                parquetFile[inc] = parquetFile[inc].astype(str).str.strip()
                parquetFile[inc] = parquetFile[inc].apply(pd.to_datetime, format='mixed',  errors='coerce') # date normalization
            if i == "str":
                for series in inc: #can only apply str to series not whole dataframes
                    parquetFile[series] = parquetFile[series].astype('string').str.replace(r'\s+', " ", regex=True).str.normalize('NFC') # string normalization (do i need to account for trailing and leading spaces?)
            if i == "bool":
                parquetFile[inc] = parquetFile[inc].astype('boolean') # bool normalization to accept no value

    parquetFile.to_parquet(filePath)
    print('File normalization complete.')
    return parquetFile #return df


