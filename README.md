# multilingual-event-pronouns

Here you will find all the materials necessary for the work presented in the paper [Exploiting Cross-Lingual Hints to Discover Event Pronouns (tentatively)](https://lrec2020.lrec-conf.org/en/).  <- enter correct link once available

This is how to extract the training data
----

1. Get the common sentences to all Europarl languages

Opus tools 

2. Get the word-aligned translations of English pronoun _it_ for a specific language

`scripts/generate-align-data.py parsed-files-dir overlapping-sentences-file language-iso-code > out-file`

example:

./generate-align-data.py ~/data/mt/v8/parsed/Europarl/parsed ~/data/mt/v8/fromOpus pt  >  enpt 

3. Get the classes for the data??

`scripts/generate-mt-data.py parsed-source-language-dir parsed-target-language-dir bitex-file alignment-output-file > out-file`

example:
./generate-mt-data.py ~/data/mt/en-fr/Europarl/parsed/en/ ~/data/mt/en-fr/Europarl/parsed/fr/ ~/data/mt/en-fr/Europarl/smt/en-fr/bitext.xml ~/data/mt/en-fr/Europarl/smt/en-fr/model/aligned.grow-diag-final-and > europarl_nom_alltrans_1kdocs 

Some additional data:
---

Besides the automatically generated data, we also include a manually annotated sample of 600 instances.






