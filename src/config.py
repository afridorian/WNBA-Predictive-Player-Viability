from pathlib import Path

#project configuration
baseDir = Path(__file__).resolve().parent.parent
dataDirRaw = baseDir / 'data' / 'raw'
dataDirCleaned = baseDir / 'data' / 'cleaned'
resultsDir = baseDir / 'results'

#league output directories
wnbaDir = dataDirRaw / 'WNBA_box_stats'
ncaaDir = dataDirRaw / 'NCAA_box_stats'

#file names
wehoopFile = 'wehoop.parquet'
scheduleFile = 'WNBA_schedules.json'
basketballRefFile = 'bbr.parquet'
combinedWNBAFile = 'combined_WNBA_player_box.parquet'
playerBiosFile = 'player_bios.parquet'
athleteIDFile = 'ESPN_athlete_ids.parquet'
espnFile = 'ESPN_NCAA_stats.parquet'
sportsRefFile = 'SR_NCAA_stats.parquet'
draftPickFile = 'draft_order.parquet'
combinedNCAAFile = 'combined_NCAA_player_box.parquet'
finalWNBAFeaturesFile = 'final_WNBA_features.parquet'
finalNCAAFeaturesFile = 'final_NCAA_features.parquet'

#load data sources configuration
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
gitHubLink = 'https://api.github.com/repos/sportsdataverse/sportsdataverse-data/releases/tags/espn_wnba_player_boxscores'
brScheduleURL = 'https://www.basketball-reference.com/wnba/years/'
brGameURL = 'https://www.basketball-reference.com'
srcbbURL = 'https://www.sports-reference.com/cbb/players/'
espnAPIURL = 'http://sports.core.api.espn.com/v2/sports/basketball/leagues/wnba/athletes/'
draftURL = 'https://www.basketball-reference.com/wnba/draft/#all_wnba_drafts'

#scrape and data cleaning variables, change here to adjust scope of data retrieval
yearsWNBAScheduleScrape = range(1997, 2004)
wehoopConcatFiles = ['player_box_2004.parquet','player_box_2005.parquet','player_box_2006.parquet','player_box_2007.parquet','player_box_2008.parquet','player_box_2009.parquet','player_box_2010.parquet','player_box_2011.parquet','player_box_2012.parquet','player_box_2013.parquet','player_box_2014.parquet','player_box_2015.parquet','player_box_2016.parquet','player_box_2017.parquet','player_box_2018.parquet','player_box_2019.parquet','player_box_2020.parquet','player_box_2021.parquet','player_box_2022.parquet','player_box_2023.parquet','player_box_2024.parquet','player_box_2025.parquet']
brConcatFiles = ['player_box_1997.parquet','player_box_1998.parquet','player_box_1999.parquet','player_box_2000.parquet','player_box_2001.parquet','player_box_2002.parquet','player_box_2003.parquet']
concatWNBAFiles = [wehoopFile,basketballRefFile]
concatNCAAFiles = [espnFile,sportsRefFile]

#feature lists - what stats will be used in the model
featureStatsWNBA = ['assist_turnover_ratio', 'assists', 'blocks', 'defensive_rebounds', 'field_goal_percentage', 'field_goals_attempted',
                          'field_goals_made','fouls','free_throw_percentage','free_throws_attempted','free_throws_made',
                          'games_started','minutes','offensive_rebounds','points','rebounds','steal_turnover_ratio','steals','three_point_field_goal_percentage',
                          'three_point_field_goals_attempted','three_point_field_goals_made','turnovers','true_shooting_percentage',
                          'three_point_attempt_rate','free_throw_attempt_rate','usage_percentage','points_per_minute','rebounds_per_minute',
                          'blocks_per_minute','steals_per_minute','turnovers_per_minute','drive_aggression','perimeter_shooting','rebound_share']

sumFeaturesNCAA = ['assists', 'blocks', 'defensive_rebounds', 'field_goals_attempted', 'field_goals_made', 'fouls', 'free_throws_attempted', 'free_throws_made', 'games_played',
                    'minutes', 'offensive_rebounds', 'points', 'rebounds', 'steals', 'three_point_field_goals_attempted', 'three_point_field_goals_made', 'turnovers']

featureStatsNCAA = ['assist_turnover_ratio', 'assists', 'blocks', 'blocks_per_minute', 'defensive_rebounds', 'drive_aggression', 'field_goal_percentage', 'field_goals_attempted',
                        'field_goals_made', 'fouls', 'free_throw_attempt_rate', 'free_throw_percentage', 'free_throws_attempted', 'free_throws_made', 'minutes', 'offensive_rebounds',
                        'perimeter_shooting', 'points', 'points_per_minute', 'rebounds', 'rebounds_per_minute', 'steal_turnover_ratio', 'steals', 'steals_per_minute', 'three_point_attempt_rate',
                        'three_point_field_goal_percentage', 'three_point_field_goals_attempted', 'three_point_field_goals_made', 'true_shooting_percentage', 'turnovers', 'turnovers_per_minute']

