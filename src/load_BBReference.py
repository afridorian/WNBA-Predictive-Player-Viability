import pandas as pd
import re
import requests
from bs4 import BeautifulSoup as bs
import random
import json
import time
import unicodedata
from datetime import datetime as dt
import config

#BASKETBALL/SPORTS REFERENCE WEB SCRAPE DATA PRE-PROCESSING FUNCTIONS
#wnba box score schedule from 1997-2003
def br_wnbaschedule_scrape(url,years,outputPath)->dict: #starting URL and years to scrape

    start = dt.now()

    headers = config.headers
    scheduleData = {}

    for i in years:
        gameData = []
        link = f'{url}/{i}_games.html'
        webPage = requests.get(link, headers=headers)

        soup = bs(webPage.content,'html.parser')  # parse the webpage using beautiful soup
        table = soup.find('table')  # find the table element using html object class
        if not table:
            raise Exception("Could not find table.")

        rows = table.find_all('tr')
        tableGrid = {}
        headersRowCount = 0
        foundDataRow = False

        for iR, row in enumerate(rows):
            if not foundDataRow:
                if row.find('td'):
                    foundDataRow = True
                else:
                    headersRowCount += 1

            cells = row.find_all(['td','a','th'])
            iC = 0

            for cell in cells:
                # Skip coordinates already occupied by a previous rowspan/colspan
                while (iR, iC) in tableGrid:
                    iC += 1

                # Safely get rowspan and colspan
                try:
                    rowspan = int(cell.get('rowspan', 1))
                except ValueError:
                    rowspan = 1

                try:
                    colspan = int(cell.get('colspan', 1))
                except ValueError:
                    colspan = 1

                if iR >= headersRowCount and iC == 7:
                    cellText = cell.find('a')['href']
                elif iR >= headersRowCount and (iC == 2 or iC == 5):
                    abbvr = cell['href']
                    team = cell.text.strip()
                    teamAbbvr = re.findall(r'\/([A-Z]+)\/',abbvr)[0]
                    cellText = (team,teamAbbvr)
                else:
                    cellText = cell.text.strip()

                for r in range(rowspan):
                    for c in range(colspan):
                        tableGrid[(iR + r, iC + c)] = cellText

                # Advance column index
                iC += colspan

        if headersRowCount == 0:
            headersRowCount = 1

        # Figure out the max number of rows and columns in the grid
        numRows = max(r for (r, c) in tableGrid.keys()) + 1 if tableGrid else 0
        numCols = max(c for (r, c) in tableGrid.keys()) + 1 if tableGrid else 0

        headersList = ['game_date','away','away_score','home','home_score','game_url']

        #Extract the data rows
        dataRange = [0, 2, 3, 5, 6, 7] #filter for wanted info
        isPlayoffs = False #set to regular season
        for r in range(headersRowCount, numRows): #loop through rows
            game = {} #set game dict
            for iC, c in enumerate(dataRange): #loop through columns with index position
                val = tableGrid.get((r, c), "") #get value
                if val == 'Playoffs': #if value is playoffs
                    isPlayoffs = True #change season type
                    break #break loop to avoid the rest of the columns
                if c == 0:
                    val = re.sub(r'\w{3}, ',"",val)
                game[headersList[iC]] = val #add val to game dict
            game['season_type'] = 2 if isPlayoffs == False else 3 #set season type
            if len(game) > 2: #if game entry is greater than 2
                gameData.append(game) #add to list

        scheduleData[i] = gameData
        print(f'{i} season completed at {dt.now().strftime("%Y-%m-%d %H:%M:%S")}.')

    with open(outputPath, 'w', encoding='utf-8') as jsonFile:
        json.dump(scheduleData, jsonFile, indent=4, ensure_ascii=False)
    end = dt.now()
    print(f'Schedule Scrape complete {end.strftime("%Y-%m-%d %H:%M:%S")} with duration of {end-start}.')
    return scheduleData

#wnba box scores from 1997-2003
def br_wnbabox_scrape(url,scheduleFile,outputPath):

    start = dt.now()
    headers = config.headers

    with open(scheduleFile,'r') as file:
        schedule = json.load(file)

    years = list(schedule.keys())
    for yr in years: #take a year a key
        gameStats = [] #each dict should be one players stats for one game use
        outputFileName = f'{outputPath}/player_box_{yr}.parquet'
        for game in schedule[yr]: #get the game dictionary from the year list
            link = f'{url}{game['game_url']}'
            time.sleep(5) #bypass site rate limiting
            webPage = requests.get(link,headers=headers)
            soup = bs(webPage.content, 'html.parser')  # parse the webpage using beautiful soup

            tableNames = [game['away'][1], game['home'][1]]
            gameID = random.randint(1000000,2000000)
            basicStats = []
            advancedStats = []

            #loop through each team on the page to get tables
            for team in tableNames:
                listOfTables = [f'box-{team}-game-basic',f'{team}-advanced']

                #loop through both tables on the page to get stats
                for tables in listOfTables:
                    table = soup.find('table',{'id': tables})  # find the table element using html object class
                    if not table:
                        raise Exception("Could not find table.")

                    rows = table.find_all('tr')
                    tableGrid = {}
                    headersRowCount = 0
                    foundDataRow = False

                    for iR, row in enumerate(rows):
                        if not foundDataRow:
                            if row.find('td'):
                                foundDataRow = True
                            else:
                                headersRowCount += 1

                        cells = row.find_all(['td', 'th'])
                        iC = 0

                        for cell in cells:
                            # Skip coordinates already occupied by a previous rowspan/colspan
                            while (iR, iC) in tableGrid:
                                iC += 1

                            # Safely get rowspan and colspan
                            try:
                                rowspan = int(cell.get('rowspan', 1))
                            except ValueError:
                                rowspan = 1

                            try:
                                colspan = int(cell.get('colspan', 1))
                            except ValueError:
                                colspan = 1

                            cellText = cell.text.strip()

                            for r in range(rowspan):
                                for c in range(colspan):
                                    tableGrid[(iR + r, iC + c)] = cellText

                            # Advance column index
                            iC += colspan

                    if headersRowCount == 0:
                        headersRowCount = 1

                    # Figure out the max number of rows and columns in the grid
                    numRows = max(r for (r, c) in tableGrid.keys()) + 1 if tableGrid else 0
                    numCols = max(c for (r, c) in tableGrid.keys()) + 1 if tableGrid else 0

                    headersList = []
                    for c in range(numCols):
                        parts = []
                        for r in range(headersRowCount):
                            part = tableGrid.get((r, c), "")
                            # Only add to the key if it isn't a duplicate (e.g., from a rowspan)
                            if part and (not parts or parts[-1] != part):
                                parts.append(part)

                        # Join the multi-level headers
                        headerName = " - ".join(parts) if parts else f"Column_{c + 1}"
                        headersList.append(headerName)

                    if 'basic' in tables:
                        basicHeaders = ['athlete_display_name', 'minutes', 'field_goals_made', 'field_goals_attempted',
                                        'field_goal_percentage', 'three_point_field_goals_made','three_point_field_goals_attempted',
                                        'three_point_field_goals_pct', 'free_throws_made','free_throws_attempted',
                                        'free_throw_percentage','offensive_rebounds', 'defensive_rebounds', 'rebounds', 'assists',
                                        'steals','blocks', 'turnovers', 'fouls','points', 'plus_minus']
                        outputHeaders = dict(zip(headersList,basicHeaders))
                        isStarter = True  # default is players are starters
                        for r in range(headersRowCount, numRows):  # loop through rows
                            if tableGrid.get((r,0),"") == 'Reserves': #check if it's a second header line
                                isStarter = False  # change player type
                                continue  # continue to the next row in the loop
                            if tableGrid.get((r, 0), "") == 'Totals': #check if it's a team totals line
                                continue #continue to next row in the loop
                            playerBasic = {}  # set player game dict
                            playerBasic['game_id'] = gameID
                            playerBasic['season'] = int(yr)
                            playerBasic['season_type'] = game['season_type']
                            playerBasic['game_date'] = game['game_date']
                            for c in range(numCols):  # loop through columns with index position
                                val = tableGrid.get((r, c), "")  # get value
                                playerBasic[outputHeaders[headersList[c]]] = val  # add val to players dict
                            playerBasic['starter'] = isStarter

                            if team in game['away']:
                                playerBasic['team_display_name'] = game['away'][0]
                                playerBasic['home_away'] = 'away'
                                playerBasic['team_winner'] = True if game['away_score'] > game['home_score'] else False
                                playerBasic['team_score'] = game['away_score']
                                playerBasic['opponent_team_display_name'] = game['home'][0]
                                playerBasic['opponent_team_score'] = game['home_score']
                            else:
                                playerBasic['team_display_name'] = game['home'][0]
                                playerBasic['home_away'] = 'home'
                                playerBasic['team_winner'] = True if game['home_score'] > game['away_score'] else False
                                playerBasic['team_score'] = game['home_score']
                                playerBasic['opponent_team_display_name'] = game['away'][0]
                                playerBasic['opponent_team_score'] = game['away_score']

                            if len(playerBasic) > 2:  # if game entry is greater than 2 and athlete display name is present
                                basicStats.append(playerBasic)  # add to list

                    else:
                        advancedHeaders = ['athlete_display_name', 'minutes', 'true_shooting_percentage',
                                           'effective_field_goal_percentage',
                                           'three_point_attempt_rate', 'free_throw_attempt_rate',
                                           'offensive_rebound_percentage',
                                           'defensive_rebound_percentage', 'total_rebound_percentage',
                                           'assist_percentage', 'steal_percentage',
                                           'block_percentage', 'turnover_percentage', 'usage_percentage',
                                           'offensive_rating', 'defensive_rating']
                        outputHeaders = dict(zip(headersList,advancedHeaders))
                        isStarter = True  # default is players are starters
                        for r in range(headersRowCount, numRows):  # loop through rows
                            if tableGrid.get((r,0),"") == 'Reserves':
                                isStarter = False  # change player type
                                continue  # continue to the next row in the loop
                            playerAdvanced = {}  # set player game dict
                            for c in range(numCols):  # loop through columns with index position
                                val = tableGrid.get((r, c), "")  # get value
                                if c == 1: #process time values
                                    if ":" in val: #if time in hours minutes format
                                        mins, sec = map(int,val.split(':'))
                                        val = round(mins + (sec/60.0),0)
                                    elif val == "": #if empty call none
                                        val = None
                                playerAdvanced[outputHeaders[headersList[c]]] = val  # add val to players dict
                            if len(playerAdvanced) > 2:  # if game entry is greater than 2
                                advancedStats.append(playerAdvanced)  # add to list

            mergeKey = {key['athlete_display_name']: key for key in basicStats}
            merge = [mergeKey[key['athlete_display_name']] | key for key in advancedStats if key['athlete_display_name'] in mergeKey]
            gameStats.extend(merge)
            print(f'{game['game_date']} {game['home'][1]} vs {game['away'][1]} completed at {dt.now().strftime("%Y-%m-%d %H:%M:%S")}.')
        df = pd.DataFrame(gameStats)
        df.to_parquet(outputFileName)
        end = dt.now()
        print(f'Basketball Reference WNBA Box Scrape complete at {end.strftime("%Y-%m-%d %H:%M:%S")} with duration of {end - start}.')
        return df

#get unique player names from WNBA and from ESPN scrape that have no NCAA stats
def get_SR_athlete_names(athleteBios,allAthletes)->set:

    #get list of bios that have no NCAA ESPN stats
    bios = athleteBios
    trueBios = bios[bios['NCAAStats']==True]
    excludeBios = set(trueBios['athlete_display_name'])

    #get list of all athlete names from WNBA data
    data = allAthletes
    players = set(data['athlete_display_name'].unique())

    #compare all missingAthletes to missingAthletes that have NCAA stats
    athletes = (players - excludeBios)
    athletes = [unicodedata.normalize('NFC',i) for i in athletes]
    athletes = sorted(athletes)

    print("Athlete names generated.")
    return athletes

#NCAA player annual stat averages from 1981-2008
def srcbb_ncaaplayer_scrape(url,players,outputPath):

    start = dt.now()
    headers = config.headers
    playerStats = []
    formattedNames = [i.lower().replace("'","").split('-', 1)[0].split(" ") for i in players] #remove ', names after hypens, and create 2 objects, first name, last name
    for iN, name in enumerate(formattedNames):  # get the player from the list of names
        x = 1
        try:
            link = f'{url}{name[0]}-{name[1]}-{x}.html'
        except IndexError:
            print(f'{players[iN]} completed with index error at {dt.now().strftime("%Y-%m-%d %H:%M:%S")}.')
            continue
        time.sleep(5)  # bypass site rate limiting
        webPage = requests.get(link, headers=headers)

        if webPage.status_code == 404: #if the call is unsuccessful
            playerStats.append({'athlete_display_name': f'{players[iN]}',"NCAAStats":False})
            print(f'{players[iN]} completed with no data found at {dt.now().strftime("%Y-%m-%d %H:%M:%S")}.')
            continue

        soup = bs(webPage.content, 'html.parser')  # parse the webpage using beautiful soup
        tableNames = ['players_per_game', 'players_totals']
        perGameAvgs = []
        seasonTotals = []
        # loop through both tables on the page to get stats
        for tables in tableNames:
            table = soup.find('table', {'id': tables})  # find the table element using html object class
            if not table:
                print(f'{players[iN]} completed with no {tables} table found at {dt.now().strftime("%Y-%m-%d %H:%M:%S")}.')
                continue

            rows = table.find_all('tr')
            tableGrid = {}
            headersRowCount = 0
            foundDataRow = False

            for iR, row in enumerate(rows):
                if not foundDataRow:
                    if row.find('td'):
                        foundDataRow = True
                    else:
                        headersRowCount += 1

                cells = row.find_all(['td', 'th'])
                iC = 0

                for cell in cells:
                    # Skip coordinates already occupied by a previous rowspan/colspan
                    while (iR, iC) in tableGrid:
                        iC += 1

                    # Safely get rowspan and colspan
                    try:
                        rowspan = int(cell.get('rowspan', 1))
                    except ValueError:
                        rowspan = 1

                    try:
                        colspan = int(cell.get('colspan', 1))
                    except ValueError:
                        colspan = 1

                    cellText = cell.text.strip()

                    for r in range(rowspan):
                        for c in range(colspan):
                            tableGrid[(iR + r, iC + c)] = cellText

                    # Advance column index
                    iC += colspan

            if headersRowCount == 0:
                headersRowCount = 1

            # Figure out the max number of rows and columns in the grid
            numRows = max(r for (r, c) in tableGrid.keys()) + 1 if tableGrid else 0
            numCols = max(c for (r, c) in tableGrid.keys()) + 1 if tableGrid else 0

            headersList = []
            for c in range(numCols):
                parts = []
                for r in range(headersRowCount):
                    part = tableGrid.get((r, c), "")
                    # Only add to the key if it isn't a duplicate (e.g., from a rowspan)
                    if part and (not parts or parts[-1] != part):
                        parts.append(part)

                # Join the multi-level headers
                headerName = " - ".join(parts) if parts else f"Column_{c + 1}"
                headersList.append(headerName)

            if 'game' in tables:
                for r in range(headersRowCount, numRows):  # loop through rows
                    if tableGrid.get((r, 0), "") == 'Career':  # check if it's a career totals line
                        break # break to the next table
                    if  tableGrid.get((r, 0), "") == '':
                        continue # continue to next row in the loop
                    perGame = {}  # set player game dict
                    perGame['athlete_display_name'] = players[iN]
                    for c in range(numCols):  # loop through columns with index position
                        columnMap = {'Season':'season', 'Class':'class', 'Pos':'athlete_position_abbreviation',
                                     'G': 'games_played', 'FG': 'avg_fg_made', 'FGA': 'avg_fg_attempt',
                                     'FG%': 'avg_fg_pct','3P': 'avg_3p_fg_made', '3PA': 'avg_3p_fg_attempt',
                                     '3P%': 'avg_3p_fg_pct','2P': 'avg_2p_fg_made', '2PA': 'avg_2p_fg_attempt',
                                     '2P%': 'avg_2p_fg_pct','eFG%': 'avg_effective_fg_pct', 'FT': 'avg_ft_made',
                                     'FTA': 'avg_ft_attempt','FT%': 'avg_ft_pct','ORB': 'avg_off_reb',
                                     'DRB': 'avg_def_reb', 'TRB': 'avg_rebs','AST': 'avg_assists',
                                     'STL': 'avg_steals','BLK': 'avg_blocks', 'TOV': 'avg_turnovers',
                                     'PF': 'avg_fouls','PTS': 'avg_points','MP': 'avg_min'}
                        if headersList[c] in columnMap.keys(): #filter out unwanted data
                            if c == 0: #format text string for season
                                val = int((tableGrid.get((r, c), ""))[:2]+(tableGrid.get((r, c), ""))[-2:])
                                if val == 1900: #account for 2000, no 20 to append the double zero to
                                    val = 2000
                            else:
                                val = tableGrid.get((r, c), "")  # get value
                            perGame[columnMap[headersList[c]]] = val  # add val to per game dict
                        else:
                            continue
                    if len(perGame) > 2:  # if game entry is greater than 2
                        perGameAvgs.append(perGame) # add to list
            else:
                for r in range(headersRowCount, numRows):  # loop through rows
                    if tableGrid.get((r, 0), "") == 'Career':  # check if it's a career totals line
                        break  # break to the next table
                    if tableGrid.get((r, 0), "") == '':
                        continue  # continue to next row in the loop
                    totals = {}  # set player game dict
                    for c in range(numCols):  # loop through columns with index position
                        columnMap = {'Season': 'season', 'Class': 'class',
                                     'G': 'games_played', 'FG': 'field_goals_made', 'FGA': 'field_goals_attempted',
                                     'FG%': 'field_goal_percentage', '3P': 'three_point_field_goals_made', '3PA': 'three_point_field_goals_attempted',
                                     '3P%': 'three_point_field_goal_percentage', '2P': 'two_point_field_goals_made', '2PA': 'two_point_field_goals_attempted',
                                     '2P%': 'two_point_field_goal_percentage', 'eFG%': 'effective_field_goal_percentage', 'FT': 'free_throws_made',
                                     'FTA': 'free_throws_attempted', 'FT%': 'free_throw_percentage', 'ORB': 'offensive_rebounds',
                                     'DRB': 'defensive_rebounds', 'TRB': 'rebounds', 'AST': 'assists',
                                     'STL': 'steals', 'BLK': 'blocks', 'TOV': 'turnovers',
                                     'PF': 'fouls', 'PTS': 'points','MP': 'minutes'}
                        if headersList[c] in columnMap.keys():  # filter out unwanted data
                            if c == 0: #format text string for season
                                val = int((tableGrid.get((r, c), ""))[:2]+(tableGrid.get((r, c), ""))[-2:])
                                if val == 1900:  # account for 2000, no 20 to append the double zero to
                                    val = 2000
                            else:
                                val = tableGrid.get((r, c), "")  # get value
                            totals[columnMap[headersList[c]]] = val  # add val to per game dict

                    if len(totals) > 2:  # if game entry is greater than 2
                        seasonTotals.append(totals)  # add to list

        mergeKey = {key['season']: key for key in perGameAvgs}
        merge = [mergeKey[key['season']] | key for key in seasonTotals if key['season'] in mergeKey]
        if len(merge) > 1:
            playerStats.extend(merge)
            print(f'{players[iN]} completed at {dt.now().strftime("%Y-%m-%d %H:%M:%S")}.')

    df = pd.DataFrame(playerStats)
    df.to_parquet(outputPath)
    end = dt.now()
    print(f'Sports Reference Scrape complete at {end.strftime("%Y-%m-%d %H:%M:%S")} with duration of {end-start}.')
    return df

