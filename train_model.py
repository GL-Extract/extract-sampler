import numpy as np
import json
from random import shuffle
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


class ModelTrainer(object):
    def __init__(self, reader, classifier="svc", split=0.8):
        """Initializes the ModelTrainer class.
        reader (list): List of file paths, features, and labels read from a
        label file.
        classifier (str): Type of classifier to use ("svc": support vector
        classifier, "logit": logistic regression, or "rf": random forest).
        split (float): Float between 0 and 1 which indicates how much data to
        use for training. The rest is used as a testing set.
        """
        self.classifier_type = classifier
        self.model = None
        self.split = split

        data = [line for line in reader.data]
        shuffle(data)
        split_index = int(split * len(data))
        train_data = data[:split_index]
        test_data = data[split_index:]
        self.X_train = np.zeros((len(train_data), reader.feature.nfeatures + 0))
        self.Y_train = np.zeros(len(train_data))

        self.X_test = np.zeros((len(test_data), reader.feature.nfeatures + 0))
        self.Y_test = np.zeros(len(test_data))

        groups = [[train_data, self.X_train, self.Y_train],
                  [test_data, self.X_test, self.Y_test]]

        for group in groups:
            raw_data, X, Y = group
            for i in range(len(raw_data)):
                x, y = reader.feature.translate(raw_data[i])
                X[i] = x
                Y[i] = y

        with open("CLASS_TABLE.json", 'w') as class_table:
            json.dump(reader.feature.class_table, class_table)

    def train(self):
        """Trains the model."""
        # TODO: as we fiddle with these, should add options to adjust classifier parameters

        if self.classifier_type == "svc":
            self.model = SVC(gamma='auto')
        elif self.classifier_type == "logit":
            self.model = LogisticRegression(multi_class='auto', solver='lbfgs')
        elif self.classifier_type == "rf":
            self.model = RandomForestClassifier(n_estimators=15,
                                                max_depth=4000,
                                                min_samples_split=3)
        self.model.fit(self.X_train, self.Y_train)

    def shuffle(self, split=None):
        """Shuffles the datasets for new trials."""
        if split is None:
            split = self.split

        old_X = np.concatenate((self.X_train, self.X_test), axis=0)
        old_Y = np.concatenate((self.Y_train, self.Y_test), axis=0)

        perm = np.random.permutation(old_Y.shape[0])

        X = old_X[perm]
        Y = old_Y[perm]

        split_index = int(split * X.shape[0])

        self.X_train = X[:split_index]
        self.Y_train = Y[:split_index]

        self.X_test = X[split_index:]
        self.Y_test = Y[split_index:]