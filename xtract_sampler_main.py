import argparse
import time
import datetime
import pickle as pkl
import json
import os

from headbytes import HeadBytes
from extpredict import NaiveTruthReader
from train_model import ModelTrainer
from test_model import score_model
from randbytes import RandBytes
from randhead import RandHead
from predict import predict_single_file, predict_directory

# Current time for documentation purposes
current_time = datetime.datetime.today().strftime('%Y-%m-%d')


def experiment(reader, classifier_name, features, trials, split, model_name):
    """Trains classifier_name on features from files in reader trials number
    of times and saves the model and returns training and testing data.

    Parameters:
    reader (list): List of file paths, features, and labels read from a
    label file.
    classifier_name (str): Type of classifier to use ("svc": support vector
    classifier, "logit": logistic regression, or "rf": random forest).
    features (str): Type of features to train on (head, rand, randhead,
    ngram, randngram).
    outfile (str): Name of file to write outputs to.
    trials (int): Number of times to train a model with randomized features
    for each training.
    split (float): Float between 0 and 1 which indicates how much data to
    use for training. The rest is used as a testing set.

    Return:
    (pkl): Writes a pkl file containing the model.
    (json): Writes a json named outfile with training and testing data.
    """
    read_start_time = time.time()
    reader.run()
    read_time = time.time() - read_start_time
    classifier = ModelTrainer(reader, classifier=classifier_name, split=split)

    for i in range(trials):
        print("Starting trial {} out of {} for {} {}".format(i, trials,
                                                             classifier_name,
                                                             features))
        classifier_start = time.time()
        print("training")
        classifier.train()
        print("done training")
        accuracy = score_model(classifier.model, classifier.X_test,
                               classifier.Y_test)
        classifier_time = time.time() - classifier_start

        outfile_name = "{}-info.json".format(os.path.splitext(model_name)[0])

        with open(model_name, "wb") as model_file:
            pkl.dump(classifier.model, model_file)
        with open(outfile_name, "a") as data_file:
            output_data = {"Classifier": classifier_name,
                           "Feature": features,
                           "Trial": i,
                           "Read time": read_time,
                           "Train and test time": classifier_time,
                           "Model accuracy": accuracy,
                           "Model size": os.path.getsize(model_name)}
            json.dump(output_data, data_file)

        if i != trials-1:
            classifier.shuffle()


def extract_sampler(classifier='rf', feature='head', model_name=None, n=1, head_bytes=512, rand_bytes=512,
                    split=0.8, label_csv=None, dirname=None, predict_file=None,
                    trained_classifier='rf-head-default.pkl', results_file='sampler_results.json'):
    if predict_file is not None:
        try:
            with open(trained_classifier, 'rb') as classifier_file:
                trained_classifier = pkl.load(classifier_file)
        except:
            print("Invalid trained classifier")

        if feature not in ["head", "rand", "randhead"]:
            print("Invalid feature option %s" % feature)
            return
        with open(results_file, 'w') as prediction_file:
            json.dump(predict_single_file(dirname, trained_classifier, feature, head_bytes=head_bytes,
                                          rand_bytes=rand_bytes), prediction_file)
        print(predict_single_file(predict_file, trained_classifier,
                                  feature))
    elif dirname is not None:
        try:
            with open(trained_classifier, 'rb') as classifier_file:
                trained_classifier = pkl.load(classifier_file)
        except:
            print("Invalid trained classifier")

        if feature not in ["head", "rand", "randhead"]:
            print("Invalid feature option %s" % feature)
            return
        with open(results_file, 'w') as prediction_file:
            json.dump(predict_directory(dirname, trained_classifier, feature, head_bytes=head_bytes,
                                        rand_bytes=rand_bytes), prediction_file)
    else:
        if classifier not in ["svc", "logit", "rf"]:
            print("Invalid classifier option %s" % classifier)
            return

        if feature == "head":
            features = HeadBytes(head_size=head_bytes)
        elif feature == "rand":
            features = RandBytes(number_bytes=rand_bytes)
        elif feature == "randhead":
            features = RandHead(head_size=head_bytes,
                                rand_size=rand_bytes)
        else:
            print("Invalid feature option %s" % feature)
            return

        if model_name is None:
            model_name = "{}-{}-trial{}-{}.pkl".format(classifier, features, current_time)

        reader = NaiveTruthReader(features, labelfile=label_csv)
        experiment(reader, classifier, feature, n,
                   split, model_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run file classification experiments')

    parser.add_argument("--dirname", type=str, help="directory of files to predict", default=None)
    parser.add_argument("--n", type=int, default=1,
                        help="number of trials", dest="n")
    parser.add_argument("--classifier", type=str,
                        help="model to use: svc, logit, rf")
    parser.add_argument("--feature", type=str, default="head",
                        help="feature to use: head, rand, randhead")
    parser.add_argument("--split", type=float, default=0.8,
                        help="test/train split ratio", dest="split")
    parser.add_argument("--head_bytes", type=int, default=512,
                        dest="head_bytes",
                        help="size of file head in bytes, default 512")
    parser.add_argument("--rand_bytes", type=int, default=512,
                        dest="rand_bytes",
                        help="number of random bytes, default 512")
    parser.add_argument("--predict_file", type=str, default=None,
                        help="file to predict based on a classifier and a "
                             "feature")
    parser.add_argument("--trained_classifier", type=str,
                        help="trained classifier to predict on",
                        default='rf-head-default.pkl')
    parser.add_argument("--results_file", type=str,
                        default="sampler_results.json", help="Name for results file if predicting")
    parser.add_argument("--label_csv", type=str, help="Name of csv file with labels",
                        default="automated_training_results/naivetruth.csv")
    parser.add_argument("--model_name", type=str, help="Name of model",
                        default=None)
    args = parser.parse_args()

    extract_sampler(args.classifier, args.feature, args.model_name, args.n, args.head_bytes,
                    args.rand_bytes, args.split, args.label_csv, args.dirname, args.predict_file,
                    args.trained_classifier, args.results_file)

