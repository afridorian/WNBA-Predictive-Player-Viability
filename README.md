# <u> WNBA Predictive Player Viability </u>
## Project Overview
The goal of this project is to build a predictive model that
estimates professional WNBA viability of current NCAA players
using decision tree modeling and ensemble learning.

The professional and collegiate game stats of WNBA players,
both current and historic, were compiled and used to train the
model. The model was segmented by three positions: guard,
forward, and center.

Player viability was defined using five tiers, which were
determined by a composite score derived from a weighted
combination of professional stats, performance metrics,
longevity in the league, and other key success indicators.
## Data Sources
| Type                       | Source                                 | Records | Date Range   | Notes                                                                                                                                                |                                                                                    
|----------------------------|----------------------------------------|---------|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| WNBA player box statistics | sportsdataverse wehoop-wnba-stats-data | 116,701 | 2002-2025    | Full game stats per player. 2004 is the first year with complete datasets. Repo is aggregation of espn.com box score game data.                      |
| WNBA player box statistics | basketball-reference.com               | 29,983  | 1997-2003    | Full game stats per player.                                                                                                                          |
| NCAA player box statistics | espn.com API                           | 1,500   | 2009-Present | Season averages and totals. 2009/10 season is the first year with complete datasets.                                                                 |
| NCAA player box statistics | sports-reference.com                   | 2,247   | 1981-Present | Season averages and totals. 1981/82 season is the first year with complete datasets. Source was used to supplement missing statistics from espn.com. |
| Draft Order                | basketball-reference.com               | 1,258   | 1997-Present | Draft pick order for players. Includes allocation draftees assigned as draft position 1.                                                             |

## Analysis
Analysis was performed in two steps.
### 1. WNBA Success Tiers
Success tiers were generated from a weighted composite score that looked at 39 features. Features normalized using 
StandardScaler within each player class and grouped into statistical categories before applying the composite score 
formula, where x represents the weight applied to those factors: 

*Scoring + Efficiency + Playmaking + Defense - Negative Performance + Position(x) + Longevity(x)*

A five tier approach was used to denote success: 

| Category       | Tier | Breakdown  |                                             
|----------------|------|------------|
| Elite          | 1    | top 10%    |
| Core Performer | 2    | 25%        |
| Bench Backups  | 3    | 25%        |
| Roster Fillers | 4    | 25%        |
| Not Viable     | 5    | bottom 15% |

### 2. Modeling

Analysis was performed using Decision Tree and Random Forest Modeling. 35 matching NCAA features were normalized using 
StandardScaler within each player class. These features were used to train both a Decision Tree and Random Forest model
using an 80/20 training/testing split. 

*Due to data source limitations, the number of games a player was a starter, rebound share, usage percentage, and game availability percentage were not included in the NCAA feature set.*

A regression analysis was performed using draft data to determine if draft position is a stronger indicator of player 
viability than the predictive models.


## Installation
No API or access keys are required to run this package.

Please install all libraries listed in the `requirements.txt` file to run modules.

## Running Analysis
From project directory select the module you would like to run. Default weights: Guards = 2, Forwards = 2, Centers = 1. 
This can be changed in `main.py` prior to execution.

### 1. Collect and Process Data
Steps 1-4. This module will scrape, clean, process, and load datasets locally:
`python src/main.py --load`

### 2. Train and Evaluate Model (Local)
Steps 5 and 6. This module will train and evaluate results using locally stored data:
`python src/main.py --evaluation`

### 3. Train and Evaluate Model (Pre-Processed)
This module will train and evaluate results using pre-processed data:
`python src/main.py --evaluation --dataURL 'https://drive.google.com/drive/folders/1gp96hX_OYUTe9Yspo4QCQyj2o4W4JSDv?usp=share_link'`

### 4. Visualization (Notebook)
Interactive results notebook; must run Modules 1 and 2 or Module 3 prior to accessing. Tune model and display output of different weight combinations:
`results.ipynb` 

### 5. Run Full Pipeline
Steps 1-6 (total run time 3 hours, 40 minutes). This module runs the entire program start to finish:
`python src/main.py --load --evaluation`

Results will appear in `results/` folder. All obtained data will be stored in `data/`

## Results
### 1. Model Performance
Decision tree performance varied across feature weightings but there was no consistent improvement pattern observed
across positions. The random forest ensemble model was sensitive to feature weighting with a clear improvement in 
prediction accuracy for guards and forwards as the weight adjusted. Centers experienced their highest accuracy 
at a weight of one, reaching the highest accuracy ceiling of all positions at 43.9%. 

Centers emerged as the most accurately predicted position across all models with forwards being the least predictable. 
This is explainable due to the nature of the position; forwards can play to both guard and center skill sets making it 
more difficult to predict them as a whole.

Overall, the ensemble model outperformed the decision tree model on all positions regardless of weighting. Both models
performed best at identifying the middle three tiers of players and struggled to accurately classify players in the Elite 
and Not Viable tiers.

### 2. Draft vs Models
A regression analysis examining the relationship between draft position and performance tier showed that draft position 
explains 24.2% of the variation in WNBA performance outcomes, not adjusted for position (*R<sup>2</sup>*=.242) with 
weighting set to 1. The mean square error showed regression predictions have an average error of one performance tier (*MSE* = 1.146).

Compared to the regression analysis, the ensemble model was able to achieve up to 44% accuracy for centers, frequently 
reaching accuracy levels in the 30% range for guards and forwards, depending on weighting. 

The NCAA feature set included in this model has a predictive power that often exceeds draft position. The ensemble model 
shows potential to support teams with draft selection by identifying performance patterns within NCAA data that are indicative 
of WNBA success.