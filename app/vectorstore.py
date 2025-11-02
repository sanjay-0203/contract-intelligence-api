# Simple in-memory TF-IDF retriever using sklearn, with persistence of chunks in DB.
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class Retriever:
    def __init__(self):
        self.vectorizer = None
        self.doc_texts = []  # list of texts (chunks)
        self.ids = []
        self.X = None

    def fit(self, texts, ids):
        # Use un-aggressive stop_words and include bigrams to improve phrase matching.
        # min_df=1 so small corpora still get vocabulary; ngram_range=(1,2) helps phrase matches.
        self.vectorizer = TfidfVectorizer(stop_words=None, lowercase=True, ngram_range=(1,2), min_df=1, max_features=20000)
        X = self.vectorizer.fit_transform(texts)
        self.doc_texts = texts
        self.ids = ids
        self.X = X

    def query(self, q, top_k=3):
        if self.vectorizer is None or len(self.doc_texts) == 0:
            return []
        vq = self.vectorizer.transform([q])
        # compute cosine-like scores via dot product (TF-IDF vectors are L2-normalized by default)
        scores = (self.X * vq.T).toarray().ravel()
        # get top_k indices even if scores are very small; we'll filter by >0 but keep small positives
        idxs = np.argsort(scores)[::-1][:top_k]
        results = []
        for i in idxs:
            score = float(scores[i])
            # include low positive scores; ignore strictly zero or negative scores
            if score <= 0:
                continue
            results.append({'id': self.ids[i], 'score': score, 'text': self.doc_texts[i]})
        return results

# single global retriever instance
RETRIEVER = Retriever()
