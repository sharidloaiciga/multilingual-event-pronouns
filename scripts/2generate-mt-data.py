#! /usr/bin/env python3
# -*- encoding: utf-8 -*-


from bs4 import BeautifulSoup
import os
import sys
import re
import logging

"""
original version of the script to extract the data in a rule-based fashion, where first one looks at en-fr, 
then en-sl or en-fi, or en-sl and en-fi. 
"""

def get_parsing(fname):

    parses = {}

    with open(fname, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")
        sentence_number = 0
        for s in soup.find_all("s"):
            sentence_number += 1
            sentence = []
            """<w xpos="NOUN" head="0" feats="Number=Sing" upos="NOUN" lemma="Resumption" id="1.1" deprel="root">
            Resumption</w>
            feats are collapsed, ex:
            feats="Mood=Ind|Tense=Pres|VerbForm=Fin"
            """
            lemma = "noLemma"
            morph = "noMorph"

            for word in s.find_all("w"):
                postag = word["upos"]
                head = word["head"]
                deprel = word["deprel"]
                position = word["id"]
                token = word.string
                if word.has_attr("lemma"):
                    lemma = word["lemma"]
                if word.has_attr("feats"):
                    morph = word["feats"]
                sentence.append((token, position, deprel, morph, head, postag, lemma))
            parses[sentence_number] = sentence
    return parses


def look_for_attached_prons(parsed_sentence, verb_head):

    children = []
    for word in parsed_sentence:
        token = word[0]
        deprel = word[2]
        head = word[4]
        if head == verb_head:
            if token.lower() == "it":
                children.append(word)
                #if "expl" in deprel:
                #    print("expletive:", word)
    return children


def look_for_attached_prons_target(parsed_sentence, verb_head):

    children = []
    for word in parsed_sentence:
        token = word[0]
        deprel = word[2]
        head = word[4]
        postag = word[5]
        if head == verb_head:
            if postag == "PRON":
                children.append(word)
    return children


def identify_src_verbs_prons(parses):
    """
    {2: [('Although', '3.1', 'advmod', 'noMorph', '3.7', 'ADV'),
     (',', '3.2', 'punct', 'noMorph', '3.7', 'PUNCT'), ...], 3: [(), ()]}
    """
    src_verbs_prons = {}

    for key in sorted(parses.keys()):
        for word in parses[key]:
            position = word[1]
            postag = word[5]
            # UD attaches predication to the adj and not the verb
            if postag in ["VERB", "AUX", "ADJ"]:
                # look_for_attached_prons_to_verb
                children = look_for_attached_prons(parses[key], position)
                if children != []:
                    if key in src_verbs_prons:
                        src_verbs_prons[key].append((word, children))
                    else:
                        src_verbs_prons[key] = [(word, children)]
    return src_verbs_prons


def find_alignment_points(list_aligns, position):

    al_points = []
    for pair in list_aligns:
        s_t = pair.split("-")
        s = int(s_t[0])
        t = int(s_t[1])
        if s == position:
            al_points.append(t)
    return al_points


def identify_alignments(src_info, alig_info):
    """
    dic{sent_id: [(verb, pron), ...], ...}

    229 [(('requested', '229.6', 'root', 'Tense=Past|VerbForm=Part|Voice=Pass', '0', 'VERB'),
    [('It', '229.1', 'nsubj:pass', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '229.6', 'PRON')])]
    """

    alignment_points = {}
    for sent_id in src_info:

        if sent_id in alig_info: # the extra language might not have the same document lenght
            aligned_sentence = alig_info[sent_id]
            for verb_pron in src_info[sent_id]:
                verb = verb_pron[0] # ('gave', '16.38', 'advcl', 'Mood=Ind|Tense=Past|VerbForm=Fin', '16.34', 'VERB')
                pronouns = verb_pron[1] # [('it', '16.37', 'nsubj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '16.38', 'PRON')]
                position_v = int(re.findall(r'(?<=\.)\d+', verb[1])[0]) - 1
                # look for position in alignments
                v_al_points = find_alignment_points(aligned_sentence, position_v)
                # verbs may be parents to more than one pronoun
                temp = []
                for pron in pronouns:
                    position_p = int(re.findall(r'(?<=\.)\d+', pron[1])[0]) - 1
                    p_al_points = find_alignment_points(aligned_sentence, position_p)
                    temp.append(p_al_points)

                if sent_id in alignment_points:
                    alignment_points[sent_id].append((v_al_points, temp))
                else:
                    alignment_points[sent_id] = [(v_al_points, temp)]
    return alignment_points


def identify_tgt_verbs_prons(parsed_sentences, alignment_points):
    """
    :param parsed_sentences: {11: [(token, position, deprel, morph, head, postag), ...], ...}
    :param alignment_points: 11 [([11], [[10]])]
    :return:

    """
    tgt_verbs_prons = {}
    for sent in alignment_points:
        parsing = parsed_sentences[sent]
        for v_p_tuple in alignment_points[sent]:
            # exs: ([6], [[5]]), ([6, 7], [[7, 9]])
            verb = v_p_tuple[0]
            prons = v_p_tuple[1]# this is a list of list

            # collect translated words aligned to the source verb
            target_verb = []
            for alignment_point in verb:
                if len(parsing) > alignment_point:
                    target_verb.append(parsing[alignment_point])

            # collect translated words aligned to the source pronouns
            target_prons = []
            for pron in prons:
                target_pron = []
                for alignment_point in pron:
                    if len(parsing) > alignment_point:
                        target_pron.append(parsing[alignment_point])
                target_prons.append(target_pron)

            # put in general dictionary
            if sent in tgt_verbs_prons:
                tgt_verbs_prons[sent].append((target_verb, target_prons))
            else:
                tgt_verbs_prons[sent] = [(target_verb, target_prons)]

    return tgt_verbs_prons


def read_bitext_correspondances(fname):

    docs_correspondances = {}
    all_doc_s_correspond = {} # src_doc_key : "src" : "tgt"

    with open(fname, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")
        for doc_linking in soup.find_all("linkGrp"):
            sentence_correspondances = {}
            src_doc = doc_linking["fromDoc"][3:-3] # "en/ep-00-01-17.xml.gz"
            tgt_doc = doc_linking["toDoc"][3:-3]
            docs_correspondances[src_doc] = tgt_doc
            for link in doc_linking.find_all("link"):
                s_correspond = link["xtargets"].split(";") # ex:"36;36", "22 23;23", "38;38 39"
                sentence_correspondances[s_correspond[0]] = s_correspond[1]
            all_doc_s_correspond[src_doc] = sentence_correspondances

    return docs_correspondances, all_doc_s_correspond


def adjust_documents(src, tgt, dic_sent_links):

    new_source = {}
    new_target = {}
    counter = 0
    for sources in dic_sent_links:
        counter += 1
        targets = dic_sent_links[sources]
        current_s = []
        curren_t = []
        for s in sources.split():
            current_s += src[int(s)]
        for t in targets.split():
            curren_t += tgt[int(t)]

        new_source[counter] = current_s
        new_target[counter] = curren_t

    return new_source, new_target



def check_target_pronouns(target_info, target_doc):
    """
    { 190: [([('temps', '196.7', 'nmod', 'Gender=Masc|Number=Sing', '196.2', 'NOUN')],
     [[('même', '196.6', 'amod', 'Gender=Masc|Number=Sing', '196.7', 'ADJ')]])], ...}
    """
    #
    improved = {} # sent_id : [((verb), (pron))]

    for sent_id in target_info:
        # example1 = ([('persévérant', '29.6', 'advcl', 'Tense=Pres|VerbForm=Part', '29.32', 'VERB')],
        # [[('Ce', '29.1', 'root', 'Number=Sing|Person=3|PronType=Dem', '0', 'PRON'),
        # ("n'", '29.2', 'advmod', 'Polarity=Neg', '29.1', 'ADV')]])
        # example2 = ([], [[]])
        # todo: these 'verbs' are the words (can be many) aligned to the src verbs

        # idea: look for pron-children of the verb

        for example in target_info[sent_id]:
            verbs = example[0]

            target_prons = []
            for verb in verbs:
                position = verb[1]
                target_prons.append(look_for_attached_prons_target(target_doc[sent_id], position))

            improved[sent_id] = (verbs, target_prons)

    return improved



def classify_instances(source_instances, target_instances):
    """
    (
    source_instances ->
    [(('received', '9.4', 'root', 'Mood=Ind|Tense=Past|VerbForm=Fin', '0', 'VERB'),
    [('it', '9.3', 'nsubj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '9.4', 'PRON')])]

    target_instanaces ->
    ([('a', '9.5', 'aux', 'Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin', '9.6', 'AUX'),
    ('bénéficié', '9.6', 'root', 'Gender=Masc|Number=Sing|Tense=Past|VerbForm=Part', '0', 'VERB')],
    [[], [('elle', '9.4', 'nsubj', 'Gender=Fem|Number=Sing|Person=3|PronType=Prs', '9.6', 'PRON')]])
    """

    pleonastic = {}
    nominals = {}
    non_nominals = {}
    # todo: I got all pronoun children of verbs in both src and tgt, how do I know who matches who?
    for sent in source_instances:

        src_examples = source_instances[sent]
        tgt_examples = target_instances[sent]

        for example in src_examples:
            src_prons = example[1] #[('it', '227.19', 'obj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '227.18', 'PRON')]
            tgt_prons = tgt_examples[1] # [[('je', '230.17', 'nsubj', 'Number=Sing|Person=1|PronType=Prs', '230.21', 'PRON'),
            # ("l'", '230.18', 'obj', 'Number=Sing|Person=3|PronType=Prs', '230.21', 'PRON')]]

            for pron in src_prons:
                deprel = pron[2]
                if "expl" in deprel:
                    for trans in tgt_prons:
                        if trans:
                            for word in trans:
                                if "nsubj" in word[2]:
                                    if sent in pleonastic:
                                        pleonastic[sent].append(pron)
                                    else:
                                        pleonastic[sent] = [pron]
                else:
                    for trans in tgt_prons:
                        if trans:
                            for word in trans:
                                if word[0].lower() in ["cela", "ça"]:
                                    if sent in non_nominals:
                                        non_nominals[sent].append(pron)
                                    else:
                                        non_nominals[sent] = [pron]
                            #    else:
                            #        if sent in nominals:
                            #            nominals[sent].append(pron)
                            #        else:
                            #            nominals[sent] = [pron]

    return pleonastic, nominals, non_nominals


def classify_multilingual(source_instances, base_lang_instances, extra_lang_instances):
    """
    (
    source_instances ->
    [(('received', '9.4', 'root', 'Mood=Ind|Tense=Past|VerbForm=Fin', '0', 'VERB'),
    [('it', '9.3', 'nsubj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '9.4', 'PRON')])]

    base_lang_instances ->
    ([('a', '9.5', 'aux', 'Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin', '9.6', 'AUX'),
    ('bénéficié', '9.6', 'root', 'Gender=Masc|Number=Sing|Tense=Past|VerbForm=Part', '0', 'VERB')],
    [[], [('elle', '9.4', 'nsubj', 'Gender=Fem|Number=Sing|Person=3|PronType=Prs', '9.6', 'PRON')]])

    extra_lang_instances ->
    ([('prejemala', '160.26', 'acl', 'Aspect=Imp|Gender=Fem|Number=Sing|VerbForm=Part', '160.21', 'VERB')],
     [[('jo', '160.24', 'obj', 'Case=Acc|Gender=Fem|Number=Sing|Person=3|PronType=Prs|Variant=Short',
      '160.26', 'PRON')]])

    """

    # todo: just keep the nominal for which I'm sure...

    pleonastic = {}
    nominals = {}
    non_nominals = {}

    lang1_examples = []
    lang1_verbs = []
    lang1_prons = []

    for sent in source_instances:

        src_examples = source_instances[sent]
        tgt_examples = base_lang_instances[sent]

        if sent in extra_lang_instances:

            lang1_examples = extra_lang_instances[sent]

        for example in src_examples:
            src_prons = example[1] #[('it', '227.19', 'obj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '227.18', 'PRON')]
            tgt_prons = tgt_examples[1] # [[('je', '230.17', 'nsubj', 'Number=Sing|Person=1|PronType=Prs', '230.21', 'PRON'),
            # ("l'", '230.18', 'obj', 'Number=Sing|Person=3|PronType=Prs', '230.21', 'PRON')]]

            if lang1_examples:

                lang1_verbs = lang1_examples[0]
                lang1_prons = lang1_examples[1]
                # print ("----->", lang1_examples)

            for pron in src_prons:
                deprel = pron[2]
                if "expl" in deprel:
                    for trans in tgt_prons:
                        if trans:
                            for word in trans:
                                if "nsubj" in word[2]:
                                    if sent in pleonastic:
                                        pleonastic[sent].append(pron)
                                    else:
                                        pleonastic[sent] = [pron]
                else:
                    for trans in tgt_prons:
                        if trans:
                            for word in trans:
                                # non-nominals
                                if word[0].lower() in ["cela", "ça"]:
                                    if sent in non_nominals:
                                        non_nominals[sent].append(pron)
                                    else:
                                        non_nominals[sent] = [pron]
                                # nominals en-fr language
                                else:
                                    #if "Masc" in word[3] or "Fem" in word[3]:
                                        # add it directly to nominals

                                        # if sent in nominals:
                                        #     nominals[sent].append(pron)
                                        # else:
                                        #     nominals[sent] = [pron]

                                        # also check sl past-participles
                                        #else

                                        # for verb in lang1_verbs:
                                        #     if "Masc" in verb[3] or "Fem" in verb[3]:
                                        #         if sent in nominals:
                                        #             nominals[sent].append(pron)
                                        #         else:
                                        #             nominals[sent] = [pron]

                                        # also check fi pronouns

                                    for pronfi in lang1_prons:
                                        if pronfi:
                                            print("====>", pronfi)
                                            print("====>", lang1_prons)
                                            for token in pronfi:
                                                if token[6] == "hän":
                                                    if sent in nominals:
                                                        nominals[sent].append(pron)
                                                    else:
                                                        nominals[sent] = [pron]
                                                # singular se (non-person) can also be used for events so exclude
                                                if token[6] == "se" and "Plur" in token[3]:
                                                    if sent in nominals:
                                                        nominals[sent].append(pron)
                                                    else:
                                                        nominals[sent] = [pron]

    return pleonastic, nominals, non_nominals




def group_multiples(d_pleo, d_nom, d_non_nom):

    # {57: [('it', '58.6', 'obl', 'Case=Acc|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '58.4', 'PRON')],
    # 256: [('it', '310.4', 'nsubj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '310.7', 'PRON')]}

    multiples = {}

    for key in d_pleo:
        for pron in d_pleo[key]:
            position = pron[1]
            if key in multiples:
                multiples[key].append((position, "pleonastic"))
            else:
                multiples[key] = [(position, "pleonastic")]

    for key in d_nom:
        for pron in d_nom[key]:
            position = pron[1]
            if key in multiples:
                multiples[key].append((position, "nominal"))
            else:
                multiples[key] = [(position, "nominal")]

    for key in d_non_nom:
        for pron in d_non_nom[key]:
            position = pron[1]
            if key in multiples:
                multiples[key].append((position, "non-nominal"))
            else:
                multiples[key] = [(position, "non-nominal")]
    return multiples


def format_doc(fname, parses, d_pleo, d_nom, d_non_nom):

    final = {}

    more_than_one = group_multiples(d_pleo, d_nom, d_non_nom)
    #  { 40: [(0, 'nominal')], 57: [(0, 'nominal'), (5, 'non-nominal'), ...], ...}

    for sent_id in sorted(parses.keys()):
        sentence = []
        if sent_id in more_than_one:
            to_label = [x[0] for x in more_than_one[sent_id]]
            for word in parses[sent_id]:
                # (token, position, deprel, morph, head, postag)
                token = word[0]
                position = parses[sent_id].index(word)
                original_position = word[1]
                postag = word[5]
                # deprel = word[2]
                # morph = word[3]
                # head = word[4]
                if original_position in to_label:
                    extracols = ["-"]*10
                    i = to_label.index(original_position)
                    label = more_than_one[sent_id][i][1]
                    last_col = ["-"]
                    temp = [fname, str(sent_id), str(position), token, postag] + extracols + [label] + last_col
                    new_line = "\t".join(temp)
                    sentence.append(new_line)
                else:
                    extracols = ["-"]*12
                    temp = [fname, str(sent_id), str(position), token, postag] + extracols
                    new_line = "\t".join(temp)
                    sentence.append(new_line)
        else:
            for word in parses[sent_id]:
                token = word[0]
                position = parses[sent_id].index(word)
                # deprel = word[2]
                # morph = word[3]
                # head = word[4]
                postag = word[5]
                extracols = ["-"]*12
                temp = [fname, str(sent_id), str(position), token, postag] + extracols
                new_line = "\t".join(temp)
                sentence.append(new_line)
        final[sent_id] = sentence
    return final


def get_alignments_for_doc(f, n_sentences):

    sent_counter = 1
    doc = {}
    while sent_counter < n_sentences+1:
        line = f.readline()
        aligns = line.strip().split()
        doc[sent_counter] = aligns
        sent_counter += 1
    return doc


def read_word_alignments(fname, sentence_links):

    language_alignments = {}

    with open(fname, "r", encoding="utf-8") as f:

        for src_file in sentence_links:
            doc = get_alignments_for_doc(f, len(sentence_links[src_file]))
            language_alignments[src_file] = doc
    return language_alignments


def main():

    if len(sys.argv) != 8:

        sys.stderr.write("Usage: {} {} {} {} {} {} {} {} \n".format(sys.argv[0], "src_parsing_data_dir", "tgt_parsing_data_dir",
                                                                    "bitext_key_file", "alignment_file",
                                                                    "sl_bitex", "sl_parse_dir", "sl_align"))
        sys.exit(1)

    logging.basicConfig(filename='generate-mt-data.log',level=logging.DEBUG)
    logging.info('Main started')

    data_src_parse_dir = sys.argv[1]
    data_tgt_parse_dir = sys.argv[2]
    bitext_key_file = sys.argv[3]
    data_alignment = sys.argv[4]
    aux_lang_bitext = sys.argv[5]
    aux_lang_parse = sys.argv[6]
    aux_lang_align = sys.argv[7]

    document_links, sentence_links = read_bitext_correspondances(bitext_key_file)
    extraL1_doclinks, extraL1_sentlinks = read_bitext_correspondances(aux_lang_bitext)
    # extraL1_doclinks, extraL1_sentlinks = {}, {}

    print("number of original en-fr documents:", len(document_links))
    print("number of original en-fi documents:", len(extraL1_doclinks))

    alignments_enfr = read_word_alignments(data_alignment, sentence_links)
    alignments_enLang1 = read_word_alignments(aux_lang_align, extraL1_sentlinks)

    files = sorted(os.listdir(data_src_parse_dir))

    # # temp = {"ep-07-09-03-015.xml", "ep-07-09-03-016.xml", "ep-07-09-03-017.xml", "ep-07-09-03-018.xml",
    #         "ep-07-09-04-003.xml", "ep-07-09-04-004.xml", "ep-07-09-04-007-08.xml", "ep-07-09-04-010.xml",
    #         "ep-07-09-04-013.xml", "ep-07-09-04-014.xml", "ep-07-09-04-015.xml", "ep-07-09-04-020.xml",
    #         "ep-07-09-04-021.xml", "ep-07-09-05-002.xml", "ep-07-09-05-011.xml", "ep-07-09-05-012.xml",
    #         "ep-07-09-05-015.xml"}

    for src_file in files:

        if src_file in document_links:
            # read alignments
            # if a document is not in bitext.xml, it shouldn't be included in the word alignment files. I checked!
            alignments = alignments_enfr[src_file]

            #if src_file in temp:

            # get parsed data
            tgt_file = document_links[src_file]
            tgt_parses = get_parsing(data_tgt_parse_dir + tgt_file)
            src_parses = get_parsing(data_src_parse_dir + src_file)

            # adjust sentence correspondence between documents
            adjusted_src, adjusted_tgt = adjust_documents(src_parses, tgt_parses, sentence_links[src_file])

            # identify source verbs & it pronouns
            # example  {16: [(('gave', '16.38', 'advcl', 'Mood=Ind|Tense=Past|VerbForm=Fin', '16.34', 'VERB'),
            # [('it', '16.37', 'nsubj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs','16.38','PRON')])],
            # ...}
            src_verbs_prons = identify_src_verbs_prons(adjusted_src)

            # identify alignment points for previous verbs & pronouns
            # example { 16: [([2], [[2]])],...}
            alignments_verbs_prons = identify_alignments(src_verbs_prons, alignments)

            # get target words correspoding to the alignment points
            # example {16: [([('les', '16.3', 'det', 'Definite=Def|Gender=Fem|Number=Plur|PronType=Art', '16.4',
            # 'DET')],[[('les', '16.3', 'det','Definite=Def|Gender=Fem|Number=Plur|PronType=Art','16.4','DET')]])],}
            tgt_verbs_prons = identify_tgt_verbs_prons(adjusted_tgt, alignments_verbs_prons)
            # todo: at this point I have the aligned pronouns to the source pronouns, but I'll use the verbs
            # todo: difference in performance if one or the other?

            # improve the pronoun alignments by using target verb info
            mono_tgt_verbs_prons = check_target_pronouns(tgt_verbs_prons, adjusted_tgt)

            # get another language to filter original examples
            #
            # I don't want to loose examples that I already have..further filter the examples
            if src_file in extraL1_doclinks:

            #print("src file in slovene ============>", src_file)
                print("src file in finnish ============>", src_file)
                alignments_lang1 = alignments_enLang1[src_file]
                lang1_fname = extraL1_doclinks[src_file]
                lang1_parses = get_parsing(aux_lang_parse + lang1_fname)
                # adhoc adjusted correspondances
                adjusted_src_lang1, adjusted_lang1 = adjust_documents(src_parses, lang1_parses,
                                                                      extraL1_sentlinks[src_file])
                # use SL to get better data

                # source_verb_pron_pairs are the same

                alignment_points_lang1 = identify_alignments(src_verbs_prons, alignments_lang1)

                tgt_pairs_lang1 = identify_tgt_verbs_prons(adjusted_lang1, alignment_points_lang1)

                mono_pairs_lang1 = check_target_pronouns(tgt_pairs_lang1, adjusted_lang1)

                # classify final instances
                pleo, nom, non_nom = classify_multilingual(src_verbs_prons, mono_tgt_verbs_prons, mono_pairs_lang1)

            else:
                # classify final instances
                # just take the  nominals
                pleo, nom, non_nom = classify_instances(src_verbs_prons, mono_tgt_verbs_prons)


                # format sentence and write document out

            f_new = open("/Users/xloish/PycharmProjects/abstract_coref/data_sharid/it-disamb/mt/en-fi-nominals/" +
                         src_file + ".conll12_format", "w", encoding="utf-8")
            first_line = "#begin document " + src_file + ";" + "\n" + "\n"
            f_new.write(first_line)

            formated_doc = format_doc(src_file, adjusted_src, pleo, nom, non_nom)

            for s in formated_doc:
                for w in formated_doc[s]:
                    f_new.write(w + "\n")
                f_new.write("\n")
            f_new.write("#end document;" + "\n")
            f_new.close()

if __name__ == "__main__":
    main()
