import config
import load_parquet as lp
import load_BBReference as bbr
import load_ESPN as es
#import load_allstar_awards as award
import processing as pr
import numpy as np
import pandas as pd
import analyze as az
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

#variables for model training
#change weight placed on viability and position specific stats in composite score; each position can we weighted independently
guardWeight = 1
forwardWeight = 1
centerWeight = 1
scaler = StandardScaler()

#determine breakpoints for composite tiering. as set, there are 5 tiers of player but can be adjusted based on use case
tierQCut = [0, 0.15, 0.40, 0.65, 0.90, 1.00]
tierLabels = [5,4,3,2,1] #must be list of int
targetNames = ['Not Viable','Roster Fillers','Bench Backups','Core Performers','Elite'] #corresponding string labels

#model tuning params
dt = DecisionTreeClassifier()
en = RandomForestClassifier(n_estimators=100, random_state=42)
testSize = .2
randomState = 42

if __name__ == "__main__":
    # STEP 1. DOWNLOAD AND CACHE WNBA DATA
    lp.download_git(config.gitHubLink, config.wnbaDir)
    bbr.br_wnbaschedule_scrape(config.brScheduleURL, config.yearsWNBAScheduleScrape,config.wnbaDir / config.scheduleFile)
    bbr.br_wnbabox_scrape(config.brGameURL, config.wnbaDir / config.scheduleFile, config.wnbaDir) #process will take 2hours 10mins for full dataset due to rate limiting
    lp.concat_files(config.wehoopConcatFiles, config.wnbaDir, config.wnbaDir / config.wehoopFile) #concat wehoop data
    lp.concat_files(config.brConcatFiles, config.wnbaDir, config.wnbaDir / config.basketballRefFile) #concat basketball reference data
    lp.normalize(config.wnbaDir / config.wehoopFile) #normalize wehoop data
    lp.normalize(config.wnbaDir / config.basketballRefFile) #normalize bbr data
    WNBAData = lp.concat_files(config.concatWNBAFiles, config.wnbaDir, config.dataDirCleaned / config.combinedWNBAFile) #combine both wnba data sources, store df as variable to work with

    # STEP 2. DOWNLOAD AND CACHE NCAA DATA
    athleteID = es.get_ESPN_athlete_id(config.dataDirCleaned / config.combinedWNBAFile, config.ncaaDir / config.athleteIDFile) #generate list of player names and espn player IDs from WNBA data
    es.ESPN_scrape(config.espnAPIURL, athleteID, config.dataDirRaw / config.playerBiosFile, config.ncaaDir / config.espnFile) #process will take 6 minutes for full dataset
    playerBios = lp.normalize(config.dataDirRaw / config.playerBiosFile) #normalize player bios
    missingAthletes = bbr.get_SR_athlete_names(playerBios, WNBAData) #get list of players with no NCAA stats
    bbr.srcbb_ncaaplayer_scrape(config.srcbbURL, missingAthletes, config.ncaaDir / config.sportsRefFile) #process will take 1 hour 10 mins for full dataset
    lp.normalize(config.ncaaDir / config.espnFile)
    lp.normalize(config.ncaaDir / config.sportsRefFile)
    lp.concat_files(config.concatNCAAFiles, config.ncaaDir, config.dataDirCleaned / config.combinedNCAAFile) #combine both ncaa data sources, store as variable (filepath) to work with or access again via data cache

    # STEP 3. DOWNLOAD DRAFT, AWARDS, AND ALL-STAR DATA
    #v2 implementation

    # STEP 4. PROCESS STATISTICS AND MISSING VALUES FOR FEATURES, DROP ATHLETES WITH MISSING NECESSARY ATTRIBUTES FROM THE DATASET
    #load cached parquets to dfs
    WNBAData = pd.read_parquet(config.dataDirCleaned / config.combinedWNBAFile)
    NCAAData = pd.read_parquet(config.dataDirCleaned / config.combinedNCAAFile)
    playerBios = pd.read_parquet(config.dataDirRaw / config.playerBiosFile)
    print('Cached files loaded.')

    # get team totals for statistics calculations
    teamTotals = pr.compute_team_totals(WNBAData)
    WNBAData = WNBAData.merge(teamTotals[['game_id', 'team_display_name', 'team_possessions', 'team_metric','team_rebounds','team_minutes']],on=['game_id', 'team_display_name'], how='outer')
    print('Team totals calculated.')

    # add back in the missing positions data and remove those players from analysis
    WNBAData = pr.get_missing_positions(WNBAData,NCAAData,playerBios)
    missingWNBAPositions = WNBAData[(WNBAData['athlete_position_abbreviation'].isna()) | (WNBAData['athlete_position_abbreviation'] == 'NA')][ 'athlete_display_name'].drop_duplicates()
    WNBAData = WNBAData[~WNBAData['athlete_display_name'].isin(missingWNBAPositions)]
    NCAAData = pr.get_missing_positions(NCAAData,playerBios)
    missingNCAAPositions = NCAAData[(NCAAData['athlete_position_abbreviation'].isna()) | (NCAAData['athlete_position_abbreviation'] == 'NA')]['athlete_display_name'].drop_duplicates()
    NCAAData = NCAAData[~NCAAData['athlete_display_name'].isin(missingNCAAPositions)]
    print('Positions normalized across all datasets.')

    # drop athletes that aren't in both the WNBA set and NCAA set
    includedAthletes = set(WNBAData['athlete_display_name'].drop_duplicates()) & set(NCAAData['athlete_display_name'].drop_duplicates())
    WNBAData = WNBAData[WNBAData['athlete_display_name'].isin(includedAthletes)]
    NCAAData = NCAAData[NCAAData['athlete_display_name'].isin(includedAthletes)]
    print(f'Total sample of WNBA players: {len(WNBAData)}. Total sample of NCAA players: {len(NCAAData)}.')

    #WNBA featuere variables
    #WNBA game level calculations
    WNBAData['field_goal_percentage'] = WNBAData['field_goal_percentage'].fillna(pr.compute_shot_pct(WNBAData,'field_goals_made','field_goals_attempted'))
    WNBAData['three_point_field_goal_percentage'] = WNBAData['three_point_field_goal_percentage'].fillna(pr.compute_shot_pct(WNBAData, 'three_point_field_goals_made', 'three_point_field_goals_attempted'))
    WNBAData['free_throw_percentage'] =  WNBAData['free_throw_percentage'].fillna(pr.compute_shot_pct(WNBAData, 'free_throws_made', 'free_throws_attempted'))
    WNBAData['true_shooting_percentage'] = WNBAData['true_shooting_percentage'].fillna(pr.compute_true_shooting_pct(WNBAData,'points','field_goals_attempted','free_throws_attempted'))
    WNBAData['three_point_attempt_rate'] = WNBAData['three_point_attempt_rate'].fillna(pr.compute_attempt_rate(WNBAData,'three_point_field_goals_attempted','field_goals_attempted'))
    WNBAData['free_throw_attempt_rate'] = WNBAData['free_throw_attempt_rate'].fillna(pr.compute_attempt_rate(WNBAData,'free_throws_attempted','field_goals_attempted'))
    WNBAData['assist_turnover_ratio'] = pr.compute_ratios(WNBAData,'assists','turnovers')
    WNBAData['steal_turnover_ratio'] = pr.compute_ratios(WNBAData, 'steals', 'turnovers')
    WNBAData['points_per_minute'] = pr.compute_ratios(WNBAData, 'points', 'minutes')
    WNBAData['rebounds_per_minute'] = pr.compute_ratios(WNBAData, 'rebounds', 'minutes')
    WNBAData['blocks_per_minute'] = pr.compute_ratios(WNBAData, 'blocks', 'minutes')
    WNBAData['steals_per_minute'] = pr.compute_ratios(WNBAData, 'steals', 'minutes')
    WNBAData['turnovers_per_minute'] = pr.compute_ratios(WNBAData, 'turnovers', 'minutes')
    WNBAData['perimeter_shooting'] = pr.compute_ratios(WNBAData, 'three_point_field_goals_attempted', 'field_goals_attempted')
    WNBAData['drive_aggression'] = pr.compute_ratios(WNBAData, 'free_throws_attempted', 'field_goals_attempted')
    WNBAData['rebound_share'] = pr.compute_ratios(WNBAData, 'rebounds', 'team_rebounds')
    WNBAData['usage_percentage'] = WNBAData['usage_percentage'].fillna((((WNBAData['field_goals_attempted'] + .44 * WNBAData['free_throws_attempted'] + WNBAData['turnovers']) *(WNBAData['team_minutes']/5))/(WNBAData['minutes']*WNBAData['team_metric']))*100).round(1)
    WNBAData[config.featureStatsAvgsWNBA] = WNBAData[config.featureStatsAvgsWNBA].apply(pd.to_numeric,errors='coerce')  # normalize numerica cols

    #Career totals then averages for final WNBA feature set
    finalWNBAFeatures = WNBAData.groupby(['athlete_display_name', 'athlete_position_abbreviation'])[config.featureStatsTotalsWNBA].mean()
    finalWNBAFeatures['total_minutes'] = WNBAData.groupby(['athlete_display_name', 'athlete_position_abbreviation'])['minutes'].sum()
    finalWNBAFeatures['games_started'] = WNBAData[WNBAData['games_started'] == True].groupby(['athlete_display_name', 'athlete_position_abbreviation']).size()
    finalWNBAFeatures['total_games'] = WNBAData[WNBAData['minutes'] > 0].groupby(['athlete_display_name', 'athlete_position_abbreviation']).size()
    finalWNBAFeatures['game_availability_percentage'] = finalWNBAFeatures['total_games'] / (WNBAData.groupby(['athlete_display_name', 'athlete_position_abbreviation', 'season'])['total_available_games'].first().groupby(['athlete_display_name', 'athlete_position_abbreviation']).sum())
    finalWNBAFeatures['total_seasons'] = WNBAData.groupby(['athlete_display_name', 'athlete_position_abbreviation'])['season'].nunique()
    finalWNBAFeatures[['games_started', 'total_minutes', 'minutes']] = finalWNBAFeatures[['games_started', 'total_minutes', 'minutes']].fillna(0)
    finalWNBAFeatures = finalWNBAFeatures.reset_index()
    finalWNBAFeatures.to_parquet(config.dataDirCleaned / config.finalWNBAFeaturesFile) #store features for visualization

    #NCAA feature variables
    #career totals then averages for the final feature set
    finalNCAAFeatures = NCAAData.groupby(['athlete_display_name', 'athlete_position_abbreviation'])[config.featureStatsNCAA].sum()
    finalNCAAFeatures['total_seasons'] = NCAAData.groupby(['athlete_display_name', 'athlete_position_abbreviation'])['season'].nunique()
    finalNCAAFeatures['total_minutes'] = finalNCAAFeatures['minutes']
    finalNCAAFeatures['field_goal_percentage'] = pr.compute_shot_pct(finalNCAAFeatures, 'field_goals_made', 'field_goals_attempted')
    finalNCAAFeatures['three_point_field_goal_percentage'] = pr.compute_shot_pct(finalNCAAFeatures, 'three_point_field_goals_made', 'three_point_field_goals_attempted')
    finalNCAAFeatures['free_throw_percentage'] = pr.compute_shot_pct(finalNCAAFeatures, 'free_throws_made', 'free_throws_attempted')
    finalNCAAFeatures['true_shooting_percentage'] = pr.compute_true_shooting_pct(finalNCAAFeatures, 'points', 'field_goals_attempted', 'free_throws_attempted')
    finalNCAAFeatures['three_point_attempt_rate'] = pr.compute_attempt_rate(finalNCAAFeatures, 'three_point_field_goals_attempted', 'field_goals_attempted')
    finalNCAAFeatures['free_throw_attempt_rate'] = pr.compute_attempt_rate(finalNCAAFeatures, 'free_throws_attempted', 'field_goals_attempted')
    finalNCAAFeatures['assist_turnover_ratio'] = pr.compute_ratios(finalNCAAFeatures, 'assists', 'turnovers')
    finalNCAAFeatures['steal_turnover_ratio'] = pr.compute_ratios(finalNCAAFeatures, 'steals', 'turnovers')
    finalNCAAFeatures['points_per_minute'] = pr.compute_ratios(finalNCAAFeatures, 'points', 'minutes')
    finalNCAAFeatures['rebounds_per_minute'] = pr.compute_ratios(finalNCAAFeatures, 'rebounds', 'minutes')
    finalNCAAFeatures['blocks_per_minute'] = pr.compute_ratios(finalNCAAFeatures, 'blocks', 'minutes')
    finalNCAAFeatures['steals_per_minute'] = pr.compute_ratios(finalNCAAFeatures, 'steals', 'minutes')
    finalNCAAFeatures['turnovers_per_minute'] = pr.compute_ratios(finalNCAAFeatures, 'turnovers', 'minutes')
    finalNCAAFeatures['perimeter_shooting'] = pr.compute_ratios(finalNCAAFeatures, 'three_point_field_goals_attempted', 'field_goals_attempted')
    finalNCAAFeatures['drive_aggression'] = pr.compute_ratios(finalNCAAFeatures, 'free_throws_attempted', 'field_goals_attempted')
    finalNCAAFeatures[config.featureStatsAvgsNCAA] = finalNCAAFeatures[config.featureStatsAvgsNCAA].astype(float).apply(pd.to_numeric, errors='coerce')  # normalize numerica cols
    finalNCAAFeatures = finalNCAAFeatures.reset_index()
    finalNCAAFeatures.loc[:, config.featureStatsAvgsNCAA] = (finalNCAAFeatures.loc[:, config.featureStatsAvgsNCAA].div(finalNCAAFeatures['games_played'].astype(float), axis=0))
    finalNCAAFeatures[['total_minutes', 'minutes']] = finalNCAAFeatures[['total_minutes', 'minutes']].fillna(0)
    finalNCAAFeatures['athlete_position_abbreviation'] = finalWNBAFeatures['athlete_position_abbreviation']
    finalNCAAFeatures.to_parquet(config.dataDirCleaned / config.finalNCAAFeaturesFile) #store features for visualization

    # STEP 5. CREATE PLAYER CLASSES AND GENERATE COMPOSITE SCORE TARGET
    #class objects are a v2 implementation for web visualization

    #split data frame to get position specific dfs and fill NA stats with median of group
    guards = finalWNBAFeatures[finalWNBAFeatures['athlete_position_abbreviation'] == 'G']
    guards = guards.replace([np.inf, -np.inf], pd.NA).fillna(guards[config.featureStatsAvgsWNBA].median())
    forwards = finalWNBAFeatures[finalWNBAFeatures['athlete_position_abbreviation'] == 'F']
    forwards = forwards.replace([np.inf, -np.inf], pd.NA).fillna(forwards[config.featureStatsAvgsWNBA].median())
    centers = finalWNBAFeatures[finalWNBAFeatures['athlete_position_abbreviation'] == 'C']
    centers = centers.replace([np.inf, -np.inf], pd.NA).fillna(centers[config.featureStatsAvgsWNBA].median())

    #z-score normalization for composite features
    guardsScaled = pd.DataFrame(scaler.fit_transform(guards[(config.featureStatsAvgsWNBA + ['total_games', 'total_minutes','total_seasons','game_availability_percentage'])]),columns=config.featureStatsAvgsWNBA + ['total_games', 'total_minutes', 'total_seasons', 'game_availability_percentage'],index=guards.index)
    forwardsScaled = pd.DataFrame(scaler.fit_transform(forwards[(config.featureStatsAvgsWNBA + ['total_games', 'total_minutes','total_seasons','game_availability_percentage'])]),columns=config.featureStatsAvgsWNBA + ['total_games', 'total_minutes', 'total_seasons', 'game_availability_percentage'],index=forwards.index)
    centersScaled = pd.DataFrame(scaler.fit_transform(centers[(config.featureStatsAvgsWNBA + ['total_games', 'total_minutes','total_seasons','game_availability_percentage'])]),columns=config.featureStatsAvgsWNBA + ['total_games', 'total_minutes', 'total_seasons', 'game_availability_percentage'],index=centers.index)

    #generate composite score and standard deviation
    guardCompositeScore = az.composite_score(guardsScaled,'guard',guardWeight)
    print(f'Guard Standard Deviation: {guardCompositeScore.std()}')
    forwardCompositeScore = az.composite_score(forwardsScaled, 'forward', forwardWeight)
    print(f'Forward Standard Deviation: {forwardCompositeScore.std()}')
    centerCompositeScore = az.composite_score(centersScaled, 'center', centerWeight)
    print(f'Center Standard Deviation: {centerCompositeScore.std()}')

    #create histograms of player performance distributions across positions
    #guards
    guardMax = np.abs(guardCompositeScore).max()
    guardBins = np.linspace(-guardMax,guardMax,10)
    guardHist = guardCompositeScore.plot(kind='hist',bins=guardBins,title="Guard Performance Distribution",xlabel='Composite Score',color='tab:orange')
    plt.savefig(f'{config.resultsDir}/guards_hist.png', dpi=300, bbox_inches='tight')
    plt.close()
    #forwards
    forwardMax = np.abs(forwardCompositeScore).max()
    forwardBins = np.linspace(-forwardMax, forwardMax, 10)
    forwardCompositeScore.plot(kind='hist', bins=forwardBins, title="Forward Performance Distribution",xlabel='Composite Score', color='tab:purple')
    plt.savefig(f'{config.resultsDir}/forwards_hist.png', dpi=300, bbox_inches='tight')
    plt.close()
    #centers
    centerMax = np.abs(centerCompositeScore).max()
    centerBins = np.linspace(-centerMax, centerMax, 10)
    centerCompositeScore.plot(kind='hist', bins=centerBins, title="Center Performance Distribution",xlabel='Composite Score', color='tab:gray')
    plt.savefig(f'{config.resultsDir}/centers_hist.png', dpi=300, bbox_inches='tight')
    plt.close()

    # determine tier cutoffs and reassign values back to original df
    guardCompositeScore = pd.DataFrame(guardCompositeScore)
    forwardCompositeScore = pd.DataFrame(forwardCompositeScore)
    centerCompositeScore = pd.DataFrame(centerCompositeScore)
    guardCompositeScore['tier'] = pd.qcut(guardCompositeScore[0],q=tierQCut,labels=tierLabels).astype(int)
    forwardCompositeScore['tier'] = pd.qcut(forwardCompositeScore[0],q=tierQCut,labels=tierLabels).astype(int)
    centerCompositeScore['tier'] = pd.qcut(centerCompositeScore[0],q=tierQCut,labels=tierLabels).astype(int)
    finalWNBAFeatures = finalWNBAFeatures.join(centerCompositeScore['tier'])
    finalWNBAFeatures['tier'] = finalWNBAFeatures['tier'].fillna(forwardCompositeScore['tier'])
    finalWNBAFeatures['tier'] = finalWNBAFeatures['tier'].fillna(guardCompositeScore['tier'])

    # STEP 6. TRAIN MODEL AND FITTING
    #separate features by position
    modelGuards = finalNCAAFeatures[finalNCAAFeatures['athlete_position_abbreviation'] == 'G']
    modelForwards = finalNCAAFeatures[finalNCAAFeatures['athlete_position_abbreviation'] == 'F']
    modelCenters = finalNCAAFeatures[finalNCAAFeatures['athlete_position_abbreviation'] == 'C']

    #guards
    gXTrain, gXTest, gYTrain, gYtest = train_test_split(modelGuards[config.featureStatsAvgsNCAA + ['total_seasons','total_minutes','games_played']],guardCompositeScore['tier'],test_size=testSize,random_state=randomState)
    dt.fit(gXTrain,gYTrain)
    gyPredDT = dt.predict(gXTest)
    accuracyGuardDT = accuracy_score(gYtest, gyPredDT)
    reportGuardDT = classification_report(gYtest, gyPredDT)
    cmGuardDT = confusion_matrix(gYtest, gyPredDT)
    print(f'Decision tree performance for Guards. Accuracy: {accuracyGuardDT}. Report: {reportGuardDT}. Confusion Matrix: {cmGuardDT}')
    en.fit(gXTrain, gYTrain)
    gyPredEN = en.predict(gXTest)
    accuracyGuardEN = accuracy_score(gYtest, gyPredEN)
    reportGuardEN = classification_report(gYtest, gyPredEN)
    cmGuardEN = confusion_matrix(gYtest, gyPredEN)
    print(f'Ensemble performance for Guards. Accuracy: {accuracyGuardEN}. Report: {reportGuardEN}. Confusion Matrix: {cmGuardEN}')

    #forwards
    fXTrain, fXTest, fYTrain, fYtest = train_test_split(modelForwards[config.featureStatsAvgsNCAA + ['total_seasons', 'total_minutes', 'games_played']],forwardCompositeScore['tier'], test_size=testSize, random_state=randomState)
    dt.fit(fXTrain, fYTrain)
    fyPredDT = dt.predict(fXTest)
    accuracyForwardDT = accuracy_score(fYtest, fyPredDT)
    reportForwardDT = classification_report(fYtest, fyPredDT)
    cmForwardDT = confusion_matrix(fYtest, fyPredDT)
    en.fit(fXTrain, fYTrain)
    fyPredEN = en.predict(fXTest)
    accuracyForwardEN = accuracy_score(fYtest, fyPredEN)
    reportForwardEN = classification_report(fYtest, fyPredEN)
    cmForwardEN = confusion_matrix(fYtest, fyPredEN)
    print(f'Decision tree performance for Forwards. Accuracy: {accuracyForwardDT}. Report: {reportForwardDT}. Confusion Matrix: {cmForwardDT}')
    print(f'Ensemble performance for Guards. Accuracy: {accuracyForwardEN}. Report: {reportForwardEN}. Confusion Matrix: {cmForwardEN}')

    #centers
    cXTrain, cXTest, cYTrain, cYtest = train_test_split(modelCenters[config.featureStatsAvgsNCAA + ['total_seasons', 'total_minutes', 'games_played']],centerCompositeScore['tier'], test_size=testSize, random_state=randomState)
    dt.fit(cXTrain, cYTrain)
    cyPredDT = dt.predict(cXTest)
    accuracyCenterDT = accuracy_score(cYtest, cyPredDT)
    reportCenterDT = classification_report(cYtest, cyPredDT)
    cmCenterDT = confusion_matrix(cYtest, cyPredDT)
    en.fit(cXTrain, cYTrain)
    cyPredEN = en.predict(cXTest)
    accuracyCenterEN = accuracy_score(cYtest, cyPredEN)
    reportCenterEN = classification_report(cYtest, cyPredEN)
    cmCenterEN = confusion_matrix(cYtest, cyPredEN)
    print(f'Decision tree performance for Forwards. Accuracy: {accuracyCenterDT}. Report: {reportCenterDT}. Confusion Matrix: {cmCenterDT}')
    print(f'Ensemble performance for Guards. Accuracy: {accuracyCenterEN}. Report: {reportCenterEN}. Confusion Matrix: {cmCenterEN}')

    # #visualizations
    positions = ['Center','Forward','Guard']
    dtViz = [accuracyCenterDT,accuracyForwardDT,accuracyGuardDT]
    enViz = [accuracyCenterEN,accuracyForwardEN,accuracyGuardEN]
    # w1DT = [29.3,23.6,30.1]
    # w15DT = [31.7,19.11,32.0]
    # w2DT = [31.7,27.9,20.6]
    # w1EN = [43.9, 26.5, 22.7]
    # w15EN = [31.7, 27.9,29.9]
    # w2EN = [39, 32.4, 36.1]
    x = np.arange(len(positions))
    width = .25
    targetNames = targetNames

    #decision tree charts
    #bar
    plt.figure(figsize=(8, 5))
    plt.bar(x - width, w1DT, width, label='Weight = 1',color='xkcd:orangeish')
    plt.bar(x, w15DT, width, label='Weight = 1.5',color='xkcd:light eggplant')
    plt.bar(x + width, w2DT, width, label='Weight = 2',color='xkcd:steel')
    plt.xticks(x, positions)
    plt.ylabel('Accuracy')
    plt.title('Decision Tree Accuracy by Position and Weight')
    plt.legend()
    plt.savefig(f'{config.resultsDir}/Decision_Tree_Accuracy.png', dpi=300, bbox_inches='tight')
    plt.close()

    #confusion matrixes
    plt.figure(figsize=(8, 6))
    sns.heatmap(cmGuardDT, annot=True, fmt='d', cmap='Oranges', xticklabels=targetNames, yticklabels=targetNames)
    plt.title(f'Guard Decision Tree Confusion Matrix - Weight {guardWeight}')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.savefig(f'{config.resultsDir}/Decision_Tree_Guard_CM_Weight{guardWeight}.png', dpi=300, bbox_inches='tight')
    plt.close()
    plt.figure(figsize=(8, 6))
    sns.heatmap(cmForwardDT, annot=True, fmt='d', cmap='Purples', xticklabels=targetNames, yticklabels=targetNames)
    plt.title(f'Forward Decision Tree Confusion Matrix - Weight {forwardWeight}')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.savefig(f'{config.resultsDir}/Decision_Tree_Forward_CM_Weight{forwardWeight}.png', dpi=300, bbox_inches='tight')
    plt.close()
    plt.figure(figsize=(8, 6))
    sns.heatmap(cmCenterDT, annot=True, fmt='d', cmap='Greys', xticklabels=targetNames, yticklabels=targetNames)
    plt.title(f'Center Decision Tree Confusion Matrix - Weight {centerWeight}')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.savefig(f'{config.resultsDir}/Decision_Tree_Center_CM_Weight{centerWeight}.png', dpi=300, bbox_inches='tight')
    plt.close()

    #ensemble charts
    #bar
    plt.figure(figsize=(8, 5))
    plt.bar(x - width, w1EN, width, label='Weight = 1', color='xkcd:orangeish')
    plt.bar(x, w15EN, width, label='Weight = 1.5', color='xkcd:light eggplant')
    plt.bar(x + width, w2EN, width, label='Weight = 2', color='xkcd:steel')
    plt.xticks(x, positions)
    plt.ylabel('Accuracy')
    plt.title('Ensemble Accuracy by Position and Weight')
    plt.legend()
    plt.savefig(f'{config.resultsDir}/Ensemble_Accuracy.png', dpi=300, bbox_inches='tight')
    plt.close()

    #confusion matrixes
    plt.figure(figsize=(8, 6))
    sns.heatmap(cmGuardEN, annot=True, fmt='d', cmap='Oranges',xticklabels=targetNames,yticklabels=targetNames)
    plt.title(f'Guard Ensemble Confusion Matrix - Weight {guardWeight}')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.savefig(f'{config.resultsDir}/Ensemble_Guard_CM_Weight{guardWeight}.png', dpi=300, bbox_inches='tight')
    plt.close()
    plt.figure(figsize=(8, 6))
    sns.heatmap(cmForwardEN, annot=True, fmt='d', cmap='Purples', xticklabels=targetNames, yticklabels=targetNames)
    plt.title(f'Forward Ensemble Confusion Matrix- Weight {forwardWeight}')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.savefig(f'{config.resultsDir}/Ensemble_Forward_CM_Weight{forwardWeight}.png', dpi=300, bbox_inches='tight')
    plt.close()
    plt.figure(figsize=(8, 6))
    sns.heatmap(cmCenterDT, annot=True, fmt='d', cmap='Greys', xticklabels=targetNames, yticklabels=targetNames)
    plt.title(f'Center Ensemble Confusion Matrix- Weight {centerWeight}')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.savefig(f'{config.resultsDir}/Ensemble_Center_CM_Weight{centerWeight}.png', dpi=300, bbox_inches='tight')
    plt.close()

    #comparison chart
    # plt.figure(figsize=(8, 5))
    # plt.bar(x - width, w2EN, width, label='Ensemble - Weight 2', color='xkcd:orangeish')
    # plt.bar(x + width, w1DT, width, label='Decision Tree - Weight 1', color='xkcd:light eggplant')
    #
    # plt.xticks(x, positions)
    # plt.ylabel('Accuracy')
    # plt.title('Model Comparison by Position')
    # plt.legend()
    # plt.savefig(f'{config.resultsDir}/Model_Comparison.png', dpi=300, bbox_inches='tight')
    # plt.close()




