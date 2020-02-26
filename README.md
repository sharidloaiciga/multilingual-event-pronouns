# multilingual-event-pronouns

Here you will find all the materials necessary for the work presented in the paper [Exploiting Cross-Lingual Hints to Discover Event Pronouns (tentatively)](https://lrec2020.lrec-conf.org/en/).  <- enter correct link once available

This is how to extract the training data
----

1. Get the common sentences to all Europarl languages using [tools from OPUS corpus.](http://opus.nlpl.eu/trac/wiki/Tools/Opus2Multi)

`opus2multi /proj/nlpl/data/OPUS/Europarl/v8/xml en es et fi fr hu it lv nl pl pt ro sk sl sv de  

find all common documents ...  
number of documents in sv: 10304  
number of documents in pt: 10344  
number of documents in et: 9035  
number of documents in it: 10412  
number of documents in hu: 8967  
number of documents in es: 10346  
number of documents in pl: 9041  
number of documents in lv: 8991  
number of documents in nl: 10345  
number of documents in fi: 10227  
number of documents in sl: 8967  
number of documents in fr: 10360  
number of documents in de: 10161  
number of documents in ro: 7502  
number of documents in sk: 8993  
number of common aligned docs: 7004  `

2. Get the word-aligned translations of English pronoun _it_ for a specific language

`./generate-align-data.py parse_dir overlap_files_dir alignment_dir source_language target_language  > out-file`

example::

./generate-align-data.py ~/data/mt/v8/parsed/Europarl/parsed ~/data/mt/v8/fromOpus ~/data/mt/v8/smt/Europarl/smt en pt  >  enpt 

3. Get the classes for the data??

`scripts/generate-mt-data.py parsed-source-language-dir parsed-target-language-dir bitex-file alignment-output-file > out-file`

example:
./generate-mt-data.py ~/data/mt/en-fr/Europarl/parsed/en/ ~/data/mt/en-fr/Europarl/parsed/fr/ ~/data/mt/en-fr/Europarl/smt/en-fr/bitext.xml ~/data/mt/en-fr/Europarl/smt/en-fr/model/aligned.grow-diag-final-and > europarl_nom_alltrans_1kdocs 

Some additional data:
---

Besides the automatically generated data, we also include a manually annotated sample of 600 instances.






