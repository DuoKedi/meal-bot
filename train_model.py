import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

df = pd.read_csv("dataset.csv")

vectorizer = TfidfVectorizer()

X = vectorizer.fit_transform(df["text"])
y = df["label"]

model = LogisticRegression(max_iter=1000)

model.fit(X, y)

joblib.dump(model, "classifier.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("Model saved")
