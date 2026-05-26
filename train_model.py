import pandas as pd
import pickle

from sklearn.neighbors import KNeighborsClassifier


def train_model():

    df = pd.read_csv(
        "dataset.csv",
        header=None
    )

    # label
    y = df.iloc[:, 0]

    # vector
    X = df.iloc[:, 1:]


    model = KNeighborsClassifier(
        n_neighbors=3
    )

    model.fit(X, y)

    with open("model.pkl", "wb") as f:

        pickle.dump(model, f)

    print("TRAIN COMPLETE")