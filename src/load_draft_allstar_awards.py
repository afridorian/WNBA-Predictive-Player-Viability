import time

import pandas as pd
import re
import requests
from bs4 import BeautifulSoup as bs
import json
import config
from datetime import datetime as dt

#SINGLE TABLE WEB SCRAPE FUNCTIONS
def draft_scrape(url,outputPath):

    start = dt.now()
    headers = config.headers
    urlList = []
    rootUrl = 'https://www.basketball-reference.com'
    link = url
    webPage = requests.get(link, headers=headers)

    soup = bs(webPage.content, 'html.parser')  # parse the webpage using beautiful soup
    table = soup.find('table',{'id':'wnba_drafts'})  # find the table element using html object class
    if not table:
        raise Exception("Could not find table.")

    rows = table.find_all('tr')
    headersRowCount = 1

    iC = 0
    for iR, row in enumerate(rows):
        cells = row.find_all(['td', 'a', 'th'])
        if iR >= headersRowCount and iC == 0:
            #put the weird little tag thing if statement here to ignore it
            cellText = cells[0].find('a')['href']
            if 'dispersal' in cellText:
                continue
            urlList.append(rootUrl+cellText)

    print('Draft URLs aggregated.')

    draftdfList = []
    allocationdfList = []

    for i in urlList:
        time.sleep(2)
        tableList = pd.read_html(i)
        pickTable = tableList[0]
        pickTable.columns = pickTable.columns.get_level_values(-1)
        if 'allocation' in i:
            allocationdfList.append(pickTable[['Team','Player']])
            print(f'Allocation draft table successfully downloaded at {dt.now().strftime("%Y-%m-%d %H:%M:%S")}.')
        else:
            draftdfList.append(pickTable[['Pk','Team','Player']])
            print(f'Draft table successfully downloaded at {dt.now().strftime("%Y-%m-%d %H:%M:%S")}.')

    draft = pd.concat(draftdfList,ignore_index=True).rename(columns={'Pk':'draft_pick','Team':'team_display_name','Player':'athlete_display_name'})
    allocationDraft = pd.concat(allocationdfList,ignore_index=True)
    allocationDraft = allocationDraft.rename(columns={'Team': 'team_display_name','Player': 'athlete_display_name'})
    draft = draft.merge(allocationDraft, how='outer',on=['athlete_display_name','team_display_name'])
    draft['draft_pick'] = draft['draft_pick'].fillna(1).apply(pd.to_numeric, errors='coerce')
    draft = draft.drop_duplicates(subset='athlete_display_name')

    draft.to_parquet(outputPath)
    end = dt.now()
    print(f'Draft data Scrape complete at {end.strftime("%Y-%m-%d %H:%M:%S")} with duration of {end - start}.')
    return draft

def allstar_scrape(url):
    pass

def awards_scrape(url):
    pass

if __name__ == "__main__":
    draftURL = config.draftURL
    allStarsURL = config.allStarsURL
    awardsURL = config.awardsURL

    draft = draft_scrape(draftURL,(config.dataDirRaw / config.draftPickFile))
    # allStar = allstar_scrape(allStarsURL)
    # awards = awards_scrape(awardsURL)