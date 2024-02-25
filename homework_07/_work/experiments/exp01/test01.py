from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

from LogisticRegression_GD_wo_tol import LogisticRegression_GD_wo_tol

import logging

logging.basicConfig(level=logging.INFO,
                    filename=f"logs/{Path(__file__).name}.log",
                    filemode="w",
                    format="%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s")

# %matplot inline
# %config InLineBackend.figure_format = 'retina'

data = pd.read_csv('data/bankloan.csv', sep=';', decimal=',', engine='pyarrow')
print(data.head())

X_train_unstandardized, X_test, y_train, y_test = train_test_split(
    data.drop('default', axis=1),
    data['default'],
    test_size=.3,
    stratify=data['default'],
    random_state=202402
)

X_train = X_train_unstandardized.copy()
num_cols = 'age debtinc creddebt othdebt'.split(' ')
logging.info(num_cols)
standartscaler = StandardScaler()
standartscaler.fit(X_train_unstandardized[num_cols])
X_train[num_cols] = standartscaler.transform(X_train_unstandardized[num_cols])
X_test = standartscaler.transform(X_test[num_cols])

X_train = pd.get_dummies(X_train)
X_test = pd.get_dummies(X_test)

print(X_train.head().T)

model = LogisticRegression_GD_wo_tol(init_method='zero', lr=.05, num_iter=10)
model.fit(X_train_unstandardized, y_train)
model.loss_visualize()
