import config
import load_parquet as lp
import load_BBReference as bbr
import load_ESPN as es
import load_draft as dr
import processing as pr
import pandas as pd
import gdown

if __name__ == "__main__":
    print("Running tests for data download:")

    # test variables
    gitLink = config.gitHubLink
    espnAPI = config.espnAPIURL
    scheduleURL = config.brScheduleURL
    wnbaGameURL = config.brGameURL
    ncaaPlayerURL = config.srcbbURL
    testFilePath = config.dataDirRaw / 'tests'
    scheduleYears = [1997]
    concatGitHub = ['player_box_2004.parquet','player_box_2005.parquet','player_box_2006.parquet']
    concatBRGit = ['player_box_1997.parquet','wehoopConcatTest.parquet']
    playerID = f'{testFilePath}/athleteID4Test.parquet'
    # missingAthletesTest = ["A'Quonesia Franklin", 'Abby Bishop', 'Adia Barnes', 'Adia Oshun Barnes',"Ji-Su Park"]
    missingAthletesTest = ['Diana Taurasi','Sue Bird','Lisa Leslie']

    #download git parquet
    print('Download files from git start.')
    lp.download_git(gitLink, testFilePath)

    #get WNBA game schedule
    print('Schedule scrape start.')
    bbr.br_wnbaschedule_scrape(scheduleURL,scheduleYears,f'{testFilePath}/1997scheduleTest.json')

    #get basketball reference WNBA box data
    print('Basketball reference WNBA box scrape start.')
    brWNBATest = bbr.br_wnbabox_scrape(wnbaGameURL,f'{testFilePath}/scheduleTest.json',f'{testFilePath}')

    #combine and normalize files
    print('Combine and normalize files start.')
    wehoopConcat = lp.concat_files(concatGitHub, testFilePath, f'{testFilePath}/wehoopConcatTest.parquet')
    lp.normalize(brWNBATest)
    lp.normalize(wehoopConcat)
    combinedSources = lp.concat_files(concatBRGit,testFilePath,f'{testFilePath}/combinedSources.parquet')
    print('Combine and normalize files end.')

    #get athlete ID and run ESPN API
    es.get_ESPN_athlete_id(f'{testFilePath}/combinedSources.parquet',f'{testFilePath}/athleteIDTest.parquet')
    print('ESPN NCAA scrape start.')
    es.ESPN_scrape(espnAPI,playerID,f'{testFilePath}/playerBios.parquet',testFilePath)

    #get athletes with athlete ID or NCAA stats from ESPN scrape
    missingAthletes = bbr.get_SR_athlete_names(f'{testFilePath}/playerBios.parquet',f'{testFilePath}/combinedSources.parquet')
    print('Sports reference NCAA scrape start.')
    bbr.srcbb_ncaaplayer_scrape(ncaaPlayerURL,missingAthletesTest,testFilePath)

    #get draft data
    dr.draft_scrape(config.draftURL, config.dataDirRaw / config.draftPickFile)
    draftData = lp.normalize(config.dataDirRaw / config.draftPickFile)

    #clean missing data from stats
    combinedSources = lp.concat_files(concatBRGit, testFilePath, f'{testFilePath}/combinedSources.parquet')
    teamTotals = pr.compute_team_totals(combinedSources,testFilePath)

    #TEST STEP 4
    #load cached parquets to dfs
    WNBAData = pd.read_parquet(config.dataDirCleaned / config.combinedWNBAFile)
    NCAAData = pd.read_parquet(config.dataDirCleaned / config.combinedNCAAFile)
    playerBios = pd.read_parquet(config.dataDirRaw / config.playerBiosFile)
    draftData = pd.read_parquet(config.dataDirRaw / config.draftPickFile)
    print('Cached files loaded.')

    #TEST STEPS 5 AND 6
    # load data
    # if args.dataURL:
    #     gdown.download_folder(args.dataURL,config.dataDirCleaned)
    finalWNBAFeatures = pd.read_parquet(config.dataDirCleaned / config.finalWNBAFeaturesFile)
    finalNCAAFeatures = pd.read_parquet(config.dataDirCleaned / config.finalNCAAFeaturesFile)

