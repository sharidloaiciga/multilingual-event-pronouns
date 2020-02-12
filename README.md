# multilingual-event-pronouns

Get the word-aligned translations of English _it_ for a specific language.

scripts/generate-align-data.py parsed-files-dir overlapping-sentences-file language-iso-code > out-file

example:

`./generate-align-data.py /Users/xloish/data/mt/v8/parsed/Europarl/parsed /Users/xloish/data/mt/v8/fromOpus pt  >  enpt `

Get the classes for the data? 

scripts/generate-mt-data.py parsed-source-language-dir parsed-target-language-dir bitex-file alignment-file > out-file

example:
`./generate-mt-data.py ~/data/mt/en-fr/Europarl/parsed/en/ ~/data/mt/en-fr/Europarl/parsed/fr/ ~/data/mt/en-fr/Europarl/smt/en-fr/bitext.xml ~/data/mt/en-fr/Europarl/smt/en-fr/model/aligned.grow-diag-final-and > europarl_nom_alltrans_1kdocs `
