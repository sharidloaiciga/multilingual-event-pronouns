#! /usr/bin/env python3
# -*- encoding: utf-8 -*-


data = open("/Users/xloish/PycharmProjects/abstract_coref/data_sharid/it-disamb/mt/en-fr-FEM/all_enfr_FEM", "r", encoding="utf-8")
new = open("/Users/xloish/PycharmProjects/abstract_coref/data_sharid/it-disamb/mt/en-fr-FEM/balanced_all_enfr_FEM", "w", encoding="utf-8")

counter_pleonastic = 0
counter_nominals = 0

# 6,193

for line in data:

    if "#" in line:
        new.write(line)
    elif line == "\n":
        new.write(line)
    else:
        cols = line.strip().split("\t")
        label = cols[15]
        if label == "-":
            new.write(line)
        elif label == "pleonastic":
            counter_pleonastic += 1
            if counter_pleonastic < 6194:
                new.write(line)
            else:
                cols[15] = "-"
                new_line = "\t".join(cols)
                new.write(new_line + "\n")
        elif label == "nominal":
            counter_nominals += 1
            if counter_nominals < 6194:
                new.write(line)
            else:
                cols[15] = "-"
                new_line = "\t".join(cols)
                new.write(new_line + "\n")
        elif label == "non-nominal":
            new.write(line)
        else:
            new.write(line)




data.close()
new.close()