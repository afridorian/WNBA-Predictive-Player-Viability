import re
import pandas as pd
import requests
from datetime import datetime as dt

#ESPN DATA PRE-PROCESSING FUNCTIONS
def ESPN_scrape(API,playerID,outputPathPlayers,outputPathStats):

    start = dt.now()

    playerBios = [] #should be a list of dictionary
    playerStats = []

    #convert df to tuple
    playerID = list(playerID.itertuples(index=False,name=None))

    for i in playerID:
        player = str(i[0]) #pull player ID from tuple
        name = i[1] #pull name from tuple

        profAthPg = requests.get(API + player).json()  # professional athlete page
        if profAthPg.get('error'):
            bio = {'athlete_display_name': name, 'error': profAthPg['error']['message']}
            playerBios.append(bio)
            print(f'{i[1]} completed with no data found.')
            continue

        # initialize the player bio
        bio = {"athlete_display_name": name,
               "athlete_id": i[0],
               "weight": None,
               "height": None,
               "DOB": None,
               "position": None,
               "athlete_position_abbreviation": None,
               "status": None,
               "totalWNBASeasons": None,
               "NCAA_athlete_id": None,
               "totalNCAASeasons": None,
               "NCAAStats": False}

        #if keys are present in profAthPg, update player entry with values
        bio["weight"] = profAthPg.get('weight'),
        bio["height"] = profAthPg.get('height'),
        bio["DOB"] = profAthPg.get('dateOfBirth')
        bio["position"] = profAthPg.get('position',{}).get('name')
        bio["athlete_position_abbreviation"] = profAthPg.get('position',{}).get('abbreviation')
        bio["status"] = profAthPg.get('status',{}).get('type')

        #reset page variables
        seasonsPg = None
        collegeAthPg = None
        collegeStatsPg = None

        #try to hit API endpoints based on keys, if they exist update player entry with values, else proceed and leave as None
        try:
            seasonsPg = requests.get(profAthPg['seasons']['$ref']).json()  # seasons played page
            bio['totalWNBASeasons'] = seasonsPg['count']
        except KeyError:
            pass
        try:
            collegeAthPg = requests.get(profAthPg['collegeAthlete']['$ref']).json() #college athlete page
            bio['NCAA_athlete_id'] = collegeAthPg['id']
            bio['totalNCAASeasons'] = collegeAthPg.get('experience',{}).get('years')
            try:
                collegeStatsPg = requests.get(collegeAthPg['statisticslog']['$ref']).json()
            except KeyError:
                pass
        except KeyError:
            pass

        if collegeStatsPg != None: #check that the collegeStatsPg returns a valid endpoint
            bio['NCAAStats'] = True

            # stats filter for player entry and normalized key names
            dictMapping = {'assistTurnoverRatio': 'assist_turnover_ratio', 'assists': 'assists',
                           'avgAssists': 'avg_assists',
                           'avgBlocks': 'avg_blocks', 'avgDefensiveRebounds': 'avg_def_reb',
                           'avgFieldGoalsAttempted': 'avg_fg_attempt',
                           'avgFieldGoalsMade': 'avg_fg_made', 'avgFouls': 'avg_fouls',
                           'avgFreeThrowsAttempted': 'avg_ft_attempt',
                           'avgFreeThrowsMade': 'avg_ft_made', 'avgMinutes': 'avg_min',
                           'avgOffensiveRebounds': 'avg_off_reb',
                           'avgPoints': 'avg_points', 'avgRebounds': 'avg_rebs', 'avgSteals': 'avg_steals',
                           'avgThreePointFieldGoalsAttempted': 'avg_3p_fg_attempt',
                           'avgThreePointFieldGoalsMade': 'avg_3p_fg_made',
                           'avgTurnovers': 'avg_turnovers', 'avgTwoPointFieldGoalsAttempted': 'avg_2p_fg_attempt',
                           'avgTwoPointFieldGoalsMade': 'avg_2p_fg_made', 'blockFoulRatio': 'block_foul_ratio',
                           'blocks': 'blocks',
                           'defensiveRebounds': 'defensive_rebounds', 'fieldGoalPct': 'field_goal_percentage',
                           'fieldGoalsAttempted': 'field_goals_attempted', 'fieldGoalsMade': 'field_goals_made',
                           'fouls': 'fouls', 'freeThrowPct': 'free_throw_percentage', 'freeThrowsAttempted': 'free_throws_attempted',
                           'freeThrowsMade': 'free_throws_made',
                           'gamesPlayed': 'games_played', 'gamesStarted': 'games_started', 'minutes': 'minutes',
                           'offensiveRebounds': 'offensive_rebounds',
                           'plusMinus': 'plus_minus', 'points': 'points', 'rebounds': 'rebounds',
                           'stealFoulRatio': 'steal_foul_ratio',
                           'stealTurnoverRatio': 'steal_turnover_ratio', 'steals': 'steals',
                           'threePointFieldGoalPct': 'three_point_field_goal_percentage',
                           'threePointFieldGoalsAttempted': 'three_point_field_goals_attempted',
                           'threePointFieldGoalsMade': 'three_point_field_goals_made',
                           'turnovers': 'turnovers',
                           'twoPointFieldGoalPct': 'two_point_field_goal_percentage', 'twoPointFieldGoalsAttempted': 'two_point_field_goals_attempted',
                           'twoPointFieldGoalsMade': 'two_point_field_goals_made'}

            for entry in collegeStatsPg['entries']: #iterates through entries dict
                for data in entry['statistics']: #iterates through list of entry objects
                    if data['type'] == 'team': #check if data is team or total stats
                        stats = requests.get(data['statistics']['$ref']).json() #call the stats endpoint
                        season = re.search(r'\d{4}',str(stats)) #get the season key from stats url using regex
                        compiledStats = {"athlete_display_name": name,'season': season.group(),"athlete_id": int(player)}
                        for cat in stats['splits']['categories']: #loop over stats categories (offense, defense, combined)
                            for output in cat['stats']: #loop over list of stat dicts
                                if output['name'] in dictMapping.keys(): #check if the stat is in the filter dict
                                    compiledStats[dictMapping[output['name']]] = output['value'] #update the stats dict with the values
                        playerStats.append(compiledStats) #update stats list with all stat values
        playerBios.append(bio)
        print(f'{i[1]} completed at {dt.now().strftime("%Y-%m-%d %H:%M:%S")}.')

    pl = pd.DataFrame(playerBios)
    pl.to_parquet(outputPathPlayers)
    st = pd.DataFrame(playerStats)
    st.to_parquet(outputPathStats)
    end = dt.now()
    print(f'ESPN Scrape complete at {end.strftime("%Y-%m-%d %H:%M:%S")} with duration of {end-start}.')
    return playerBios

def get_ESPN_athlete_id(filePath,outputPath):
    data = pd.read_parquet(filePath)
    players = data[['athlete_id','athlete_display_name']].drop_duplicates().dropna() #get unique player names and athlete IDs
    players = players.groupby('athlete_id')['athlete_display_name'].agg(lambda x: ', '.join(x.astype(str))).reset_index() #if athlete IDs appear more than once, create a list in the player name column of each player associated with the id
    players.to_parquet(outputPath)
    print('Get ESPN athlete ID complete.')
    return players

