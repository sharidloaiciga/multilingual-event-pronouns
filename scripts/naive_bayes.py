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



def import_manual_data(dir_name, n_examples):

    languages = ["600_man_classes", "600_es", "600_et", "600_fi", "600_fr", "600_hu", "600_it", "600_lv", "600_man_classes", "600_nl",
                 "600_pl", "600_pt", "600_ro", "600_sk", "600_sl", "600_sv"]

    # ["600_es", "600_et", "600_fi", "600_fr", "600_hu", "600_it", "600_lv", "600_man_classes", "600_nl",
    # "600_pl", "600_pt", "600_ro", "600_sk", "600_sl", "600_sv"]

    features = np.chararray((n_examples, len(languages)), itemsize=10) # itemsize = wordsize
    Ys = []
    for i in range(len(languages)):
        lang = languages[i]
        row = 0
        with open(dir_name + "/" + lang, "r", encoding="utf-8") as f:
            for line in f:
                #   0
                # alors
                if lang == "600_man_classes":
                    classification = line.strip("\n").replace(" ", "")
                    Ys.append(classification)
                else:
                    trans = line.strip("\n").replace(" ", "")
                    features[row, i] = trans.encode('utf-8')
                    row += 1

    features_list = features.tolist()
    return features, Ys



def import_auto_data(dir_name, n_examples):

    languages = os.listdir(dir_name)

    features = np.chararray((n_examples, len(languages)), itemsize=10) # itemsize = wordsize
    Ys = []
    for i in range(len(languages)):
        lang = languages[i]
        row = 0
        with open(dir_name + "/" + lang, "r", encoding="utf-8") as f:
            for line in f:
                #         0               1        2      3         4              5
                # ep-09-01-12-012.xml 	 18 	 46.1 	 it 	 unknown_ref 	 alors
                cols = line.strip("\n").split("\t")
                if "en_fr" in lang:
                    classification = cols[4].replace(" ", "")
                    Ys.append(classification)
                else:
                    trans = cols[-1].replace(" ", "") # different column if I use noUNK !!!
                    features[row, i] = trans.encode('utf-8')
                row += 1
    features_list = features.tolist()
    return features_list, Ys


def main():

    # data_dir = "/Users/xloish/PycharmProjects/abstract_coref/data_sharid/it-disamb/mt/2ndround/multilingual/noUNK"
    data_dir = "/Users/xloish/PycharmProjects/abstract_coref/data_sharid/it-disamb/mt/2ndround/" \
               "multilingual_improved_align/noUNK"

    # n_examples = 69431  # multilingual with unknown_ref class f
    # n_examples = 17534 # multilingual all without unknown_ref class
    n_examples = 22736 # multilingual_improved_aling without unknown_ref

    #x, y = import_manual_data(data_dir, n_examples)
    x, y = import_auto_data(data_dir, n_examples)


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