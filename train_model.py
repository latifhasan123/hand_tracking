import pandas as pd
import pickle

from sklearn.neighbors import KNeighborsClassifier


def train_model():

    # =========================
    # LOAD DATASET
    # =========================
    df = pd.read_csv(
        "dataset.csv",
        header=None
    )

    # label
    y = df.iloc[:, 0]

    # vector
    X = df.iloc[:, 1:]

    # =========================
    # MODEL
    # =========================
    model = KNeighborsClassifier(
        n_neighbors=3
    )

    model.fit(X, y)

    # =========================
    # SAVE MODEL
    # =========================
    with open("model.pkl", "wb") as f:

        pickle.dump(model, f)

    print("TRAIN COMPLETE")