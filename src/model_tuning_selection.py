from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
import xgboost as xgb
from sklearn.pipeline import Pipeline

#should test SMOTE here as well

cv = StratifiedKFold(n_splits=5,shuffle=True,random_state=14)
dt = DecisionTreeClassifier(random_state=14)
en = RandomForestClassifier(n_estimators=100, random_state=14)
#xgboost classifier using pipeline