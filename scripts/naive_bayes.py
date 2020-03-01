#! /usr/bin/env python3
# -*- encoding: utf-8 -*-

from sklearn import preprocessing
from sklearn.metrics import classification_report
from sklearn.tree.export import export_text
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
import re
import os
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

def main():

    if len(sys.argv) != 2:
        sys.stderr.write("Usage: {} {} \n".format(sys.argv[0], "training_data_dir"))
        sys.exit(1)

    # directory containing data
    data_dir = sys.argv[1]

    #x, y = import_manual_data(data_dir, n_examples)
    x, y = import_data(data_dir)


    # encode and transform traing data


    f_enc = preprocessing.OrdinalEncoder()
    f_enc.fit(x)
    features = f_enc.transform(x)

    l_enc = preprocessing.LabelEncoder()
    l_enc.fit(y)
    labels = l_enc.transform(y)

    # transform test data

    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.3,shuffle=True,random_state=109) # 70% training and 30% test

    # train

    gnb = GaussianNB()
    gnb = gnb.fit(X_train, y_train)

    # test

    prediction = gnb.predict(X_test)
    gold = y_test

    print("label categories ==>")
    print(l_enc.classes_) # categories of labels

    print("prediction ==> ", prediction)
    print("gold ===>", gold)
    print(classification_report(gold, prediction))

    # interpretability

    # interpret(f_enc, clf)




if __name__ == "__main__":
    main()