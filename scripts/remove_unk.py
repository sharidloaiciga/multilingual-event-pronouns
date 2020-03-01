#! /usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
filter unknown_reference examples from all language files
"""

import os
import sys

def get_key(in_dir_name):

    no_unks = []
    languages = os.listdir(in_dir_name)
    classes_file = languages[1][:-2] + "fr"
    counter = 0
    with open(data_dir + classes_file, "r", encoding="utf-8") as french:
        for line in french:
            counter += 1
            cols = line.strip().split("\t")
            if "fr" in lang:
                classification = cols[4].replace(" ", "")
                if classification != "unknown_ref":
                    no_unks.append(counter)
    french.close()
    return no_unks


data_dir = sys.argv[1]
out_dir = sys.argv[2]

valid_sentences = get_key(data_dir)
languages = os.listdir(data_dir)


for lang in languages:
    with open(data_dir + "/" + lang, "r", encoding="utf-8") as in_f:
        counter2 = 0
        new_no_unks = open(out_dir + "/" + lang, "w", encoding="utf-8")
        for line in in_f:
            counter2 += 1
            if counter2 in valid_sentences:
                new_no_unks.write(line)
        new_no_unks.close()
        in_f.close()
