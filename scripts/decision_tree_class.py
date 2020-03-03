#! /usr/bin/env python3
# -*- encoding: utf-8 -*-

from sklearn import tree
from sklearn import preprocessing
from sklearn.metrics import classification_report
from sklearn.tree.export import export_text
from sklearn.model_selection import train_test_split

from imblearn.under_sampling import ClusterCentroids
from imblearn.over_sampling import RandomOverSampler
from collections import Counter
import re
import os
import sys
import numpy as np



def get_num_examples(dir_name):

    languages = os.listdir(dir_name)
    classes_file = languages[1][:-2] + "fr"
    num_lines = sum(1 for line in open(dir_name + "/" + classes_file, "r", encoding="utf-8"))
    print("number of examples:", num_lines)
    return num_lines


def import_data(dir_name):

    languages = os.listdir(dir_name)
    n_examples = get_num_examples(dir_name)
    features = np.chararray((n_examples, len(languages)), itemsize=12) # itemsize = wordsize
    Ys = []

    for i in range(len(languages)):
        lang = languages[i][-2:]
        with open(dir_name + "/" + languages[i], "r", encoding="utf-8") as f:
            row = 0
            for line in f:
                cols = line.strip("\n").split("\t")
                if lang == "fr":
                    #      0                 1    2      3            4           5
                    # ep-09-01-12-012.xml 	 3 	 11.5 	 it 	 unknown_ref 	 empty
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
    n_examples = get_num_examples(dir_name)
    features = np.chararray((n_examples, len(languages)), itemsize=12) # itemsize = wordsize
    Ys = []
    for i in range(len(languages)):
        lang = languages[i][-2:]
        row = 0
        with open(dir_name + "/" + languages[i], "r", encoding="utf-8") as f:
            for line in f:
                cols = line.strip("\n").split("\t")
                if lang == "fr":
                    #      0                 1    2      3            4           5
                    # ep-09-01-12-012.xml 	 3 	 11.5 	 it 	 unknown_ref 	 empty
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


def interpret(f_enc, clf):

    print("feature categories ==>")
    print(f_enc.categories_) # categories of features

    c = 0
    features_dict = {}
    for l in f_enc.categories_:
        for feat in l:
            features_dict[c] = feat
            c += 1

    # draw tree
    r = export_text(clf)

    createtree = open("tree.txt", "w", encoding="utf-8")
    createtree.write(r)
    createtree.close()

    prettytree = open("tree.txt", "r", encoding="ISO-8859-1")

    for line in prettytree:
        id = re.findall(r'feature_([0-9]*)', line)
        if id:
            id_id = id[0]
            word = features_dict[int(id_id)].decode("utf-8")
            new_line = line.replace('feature_'+id_id, word).strip()
            print(new_line)
        else:
            print(new_line)
    prettytree.close()



def main():

    if len(sys.argv) != 3:
        sys.stderr.write("Usage: {} {} {} \n".format(sys.argv[0], "training_data_dir", "test_dir"))
        sys.exit(1)

    # directory containing data
    data_dir = sys.argv[1]
    test_dir = sys.argv[2]

    # import data
    x, y = import_data(data_dir)

    print(len(x), len(y))

    # print("********************")
    # this is just to print some examples for the presentation
    #
    # for each in x[50:70]:
    #     temp = []
    #     for word in each:
    #         try:
    #             word.decode("utf-8")
    #             temp.append(word.decode("utf-8"))
    #         except UnicodeError:
    #             temp.append(word)
    #     print(temp)
    # print(y[50:70])


    # encode and transform training data

    f_enc = preprocessing.OneHotEncoder(handle_unknown="ignore")
    f_enc.fit(x)
    features = f_enc.transform(x)

    l_enc = preprocessing.LabelEncoder()
    l_enc.fit(y)
    labels = l_enc.transform(y)

    # transform new test data
    x_manual, y_manual = import_manual_data(test_dir)

    # print(len(x_manual), len(y_manual))

    unseen_feats = f_enc.transform(x_manual)
    unseen_labels = l_enc.transform(y_manual)

    # undersampling
    # cc = ClusterCentroids(random_state=0)
    # X_resampled, y_resampled = cc.fit_resample(features, labels)

    # oversampling
    ros = RandomOverSampler(random_state=0)
    X_resampled, y_resampled = ros.fit_resample(features, labels)

    print("resampled y's", sorted(Counter(y_resampled).items()))

    # spliting

    # use with resampling

    # oversampling
    ros = RandomOverSampler(random_state=0)
    X_resampled, y_resampled = ros.fit_resample(features, labels)

    # resampling
    # X_train, X_test, y_train, y_test = train_test_split(X_resampled, y_resampled, test_size=0.3,shuffle=True,random_state=109)
    # print("resampled items:", sorted(Counter(y_resampled).items()))

    # X_new = SelectKBest(mutual_info_classif).fit_transform(features, labels)

    # no resampling
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.3, shuffle=True, random_state=109)

    print("splitted train items:", sorted(Counter(y_train).items()))
    print("splitted test items:", sorted(Counter(y_test).items()))

    # train
    clf = tree.DecisionTreeClassifier()
    clf = clf.fit(X_train, y_train)

    print( "=====>", X_train.shape[0], y_test.shape[0])
    # # test

    prediction = clf.predict(unseen_feats) #X_test
    gold = unseen_labels # y_test

    #prediction = clf.predict(X_test) #X_test
    #gold = y_test # y_test

    print("features_importances ==>")
    print(clf.feature_importances_)

    # spliting



    # test
    # print(sorted(Counter(y_resampled).items()))
    # test on either X_test/y_test or unseen_feats/unseen_labels

    pred_automatic = clf.predict(X_test)
    gold_automatic = y_test

    pred_manual = clf.predict(unseen_feats)
    gold_manual = unseen_labels


    print("label categories ==>")

    print(l_enc.classes_) # categories of labels

    mapping = get_integer_mapping(l_enc)
    print("event:", mapping["event_ref"])
    print("nominal:", mapping["nominal_ref"])
    print("pleo:", mapping["pleonastic_ref"])

    print("**results test on automatic annotation**")
    print("prediction ==> ", pred_automatic)
    print("gold ===>", gold_automatic)
    print(classification_report(gold_automatic, pred_automatic))

    print("**results test on manual annotation**")
    print("prediction ==> ", pred_manual)
    print("gold ===>", gold_manual)
    print(classification_report(gold_manual, pred_manual))


    #
    # # # draw tree
    #
    interpret(f_enc, clf)



if __name__ == "__main__":
    main()
