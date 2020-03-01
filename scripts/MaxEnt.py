#! /usr/bin/env python3
# -*- encoding: utf-8 -*-

from sklearn import preprocessing
from sklearn.metrics import classification_report
from sklearn.tree.export import export_text
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

from imblearn.under_sampling import ClusterCentroids
from imblearn.over_sampling import RandomOverSampler



import re
import os
import numpy as np
import sys



def get_num_examples(dir_name):

    languages = os.listdir(dir_name)
    classes = languages[1][:-2] + "fr"
    n_examples = 0
    noUNKs = 0
    with open(dir_name + "/" + classes, "r", encoding="utf-8") as f:
        for line in f:
            n_examples += 1
            cols =  line.strip("\n").split("\t")
            label = cols[4]
            if label != "unknown_ref":
                noUNKs += 1
    f.close()

    print("total examples w UNK_ref:", n_examples)
    print("total examples w/o UNK_ref:", noUNKs)
    return n_examples, noUNKs


def import_data(dir_name, UNK):

    languages = os.listdir(dir_name)
    total_examples, noUNK_examples = get_num_examples(dir_name)

    if UNK == "yes":
        n_examples = total_examples
    else:
        n_examples = noUNK_examples

    features = np.chararray((n_examples, len(languages)), itemsize=12) # itemsize = wordsize
    Ys = []

    for i in range(len(languages)):
        lang = languages[i][-2:]
        row = 0

        with open(dir_name + "/" + languages[i], "r", encoding="utf-8") as f:
            for line in f:
                #      0                 1    2      3            4           5
                # ep-09-01-12-012.xml 	 3 	 11.5 	 it 	 unknown_ref 	 empty
                cols = line.strip("\n").split("\t")

                if lang == "fr":
                    classification = cols[4].replace(" ", "")
                    Ys.append(classification)
                else:
                    #      0                 1    2      3
                    # ep-09-01-12-012.xml 	 3 	 11.5 	 ganz
                    trans = cols[-1].replace(" ", "")
                    features[row, i] = trans.encode('utf-8')
                row += 1
    return features, Ys


def import_manual_data(dir_name):

    languages = os.listdir(dir_name)
    n_examples = sum(1 for line in open(dir_name + "/" + languages[1], "r", encoding="utf-8"))
    features = np.chararray((n_examples, len(languages)), itemsize=12) # itemsize = wordsize
    Ys = []
    for i in range(len(languages)):
        lang = languages[i][-2:]
        row = 0

        with open(dir_name + "/" + languages[i], "r", encoding="utf-8") as f:
            for line in f:
                #      0                 1    2      3            4           5        6
                # ep-09-01-12-012.xml 	 3 	 11.5 	 it 	 unknown_ref 	 empty     nominal_ref
                cols = line.strip("\n").split("\t")

                if lang == "fr":
                    classification = cols[-1].replace(" ", "")
                    Ys.append(classification)
                else:
                    #      0                 1    2      3
                    # ep-09-01-12-012.xml 	 3 	 11.5 	 ganz
                    trans = cols[-1].replace(" ", "")
                    features[row, i] = trans.encode('utf-8')
                row += 1
    return features, Ys



def get_integer_mapping(le):
    '''
    Return a dict mapping labels to their integer values
    from an sklearn LabelEncoder
    le = a fitted sklearn LabelEncoder
    '''
    res = {}
    for cl in le.classes_:
        res.update({cl:le.transform([cl])[0]})
    return res


def main():

    if len(sys.argv) != 2:
        sys.stderr.write("Usage: {} {} \n".format(sys.argv[0], "training_data_dir"))
        sys.exit(1)

    # directory containing data
    data_dir = sys.argv[1]

    # import data
    x, y = import_data(data_dir, UNK="no")
    # x, y = import_manual_data(data_dir, n_examples)

    # encode and transform training data
    f_enc = preprocessing.OneHotEncoder(handle_unknown="ignore")
    f_enc.fit(x)
    features = f_enc.transform(x)

    l_enc = preprocessing.LabelEncoder()
    l_enc.fit(y)
    labels = l_enc.transform(y)

    # transform new test data
    # unseen_data = "/Users/xloish/PycharmProjects/abstract_coref/data_sharid/it-disamb/mt/2ndround/" \
    #              "multilingual_improved_align/"
    # auto_and_man = "/Users/xloish/PycharmProjects/abstract_coref/data_sharid/it-disamb/mt/2ndround/" \
    #              "multilingual_improved_align/onlyGOLD_fromAUTOMATIC"

    # x_unseen_test, y_unseen_test = import_manual_data(unseen_data, 600)
    # x_unseen_test, y_unseen_test = import_data(auto_and_man, 182, unseen=False)

    # print(len(x_unseen_test), len(y_unseen_test))

    # unseen_feats = f_enc.transform(x_unseen_test)
    # unseen_labels = l_enc.transform(y_unseen_test)

    # undersampling
    # cc = ClusterCentroids(random_state=0)
    # X_resampled, y_resampled = cc.fit_resample(features, labels)

    # oversampling
    ros = RandomOverSampler(random_state=0)
    X_resampled, y_resampled = ros.fit_resample(features, labels)

    # print(sorted(Counter(y_resampled).items()))

    # spliting

    X_train, X_test, y_train, y_test = train_test_split(X_resampled, y_resampled, test_size=0.3,shuffle=True,random_state=109)

    # X_new = SelectKBest(mutual_info_classif).fit_transform(features, labels)

    # X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.3,shuffle=True,random_state=109)

    #print("X before split")


    #print("X_train after split")
    #print(X_train)


    #print("X_train after selection")
    #print(X_new)


    # train

    # C=0.001, penalty="l2",
    clf = LogisticRegression(random_state=0, solver='newton-cg', multi_class='multinomial', max_iter=1000)
    clf = clf.fit(X_train, y_train)

    # test

    #print(sorted(Counter(y_resampled).items()))
    #
    prediction = clf.predict(X_test)
    gold = y_test

    # test_new = SelectKBest(mutual_info_classif).fit_transform(unseen_feats, unseen_labels)
    # prediction = clf.predict(unseen_feats)
    # prediction = clf.predict(test_new)
    # gold = unseen_labels


    print("label categories ==>")
    print(l_enc.classes_) # categories of labels
    mapping = get_integer_mapping(l_enc)
    print("event:", mapping["event_ref"])
    print("nominal:", mapping["nominal_ref"])
    print("pleo:", mapping["pleonastic_ref"])

    print("prediction ==> ", prediction)
    print("gold ===>", gold)
    print(classification_report(gold, prediction))







if __name__ == "__main__":
    main()