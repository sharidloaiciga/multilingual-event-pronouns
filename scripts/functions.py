
from bs4 import BeautifulSoup
import re


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
            for word in s.find_all("w"):
                postag = word["upos"]
                head = word["head"]
                deprel = word["deprel"]
                position = word["id"]
                token = word.string
                if word.has_attr("feats"):
                    morph = word["feats"]
                else:
                    morph = "noMorph"
                sentence.append((token, position, deprel, morph, head, postag))
            parses[sentence_number] = sentence
    return parses


def attached_src_prons(parsed_sentence, verb_head):

    children = []
    for word in parsed_sentence:
        token = word[0]
        head = word[4]
        pos = word[5]
        if head == verb_head:
            if token.lower() in ["it"] and pos == "PRON":
                children.append(word)
                #if "expl" in deprel:
                #    print("expletive:", word)
    return children


def identify_src_verbs_prons(parses):
    """
    {2: [('Although', '3.1', 'advmod', 'noMorph', '3.7', 'ADV'),
     (',', '3.2', 'punct', 'noMorph', '3.7', 'PUNCT'), ...], 3: [(), ()]}
    """
    srcVerbs = {}
    srcProns = {}

    for key in sorted(parses.keys()):
        for word in parses[key]:
            position = word[1]
            postag = word[5]
            # UD attaches predication to the adj and not the verb
            if postag in ["VERB", "ADJ"]: # not including "AUX" risks excluding exs like 'He did it" # not ADJ
                # look_for_attached_prons_to_verb
                children = attached_src_prons(parses[key], position)
                if children:
                    if key in srcVerbs:
                        srcVerbs[key].append(word)
                        srcProns[key].append(children)
                    else:
                        srcVerbs[key] = [word]
                        srcProns[key] = [children]

    return srcVerbs, srcProns


def find_alignment_points(list_aligns, position):

    al_points = []
    for pair in list_aligns:
        s_t = pair.split("-")
        s = int(s_t[0])
        t = int(s_t[1])
        if s == position:
            al_points.append(t)
    return al_points


def identify_prons_alignment_points(info_src, alig_info):
    """
    src_verbs -> {16: [('gave', '16.38', 'advcl', 'Mood=Ind|Tense=Past|VerbForm=Fin', '16.34', 'VERB')...] ...,
    src_prons -> {16: [[('it', '16.37', 'nsubj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs',
    '16.38','PRON')], ...], ...}
    """

    alignment_points_prons = {}

    for sent_id in info_src:
        aligned_sentence = alig_info[sent_id]
        for pron_list in info_src[sent_id]:
            aligns = []
            for pron in pron_list:
                position_p = int(re.findall(r'(?<=\.)\d+', pron[1])[0]) - 1
                # look for position in alignments
                align_points = find_alignment_points(aligned_sentence, position_p)
                aligns.append(align_points)

            if sent_id in alignment_points_prons:
                alignment_points_prons[sent_id].append(aligns)
            else:
                alignment_points_prons[sent_id] = [aligns]
    return alignment_points_prons


def identify_verbs_alignment_points(info_src, alig_info):
    """
    src_verbs -> {16: [('gave', '16.38', 'advcl', 'Mood=Ind|Tense=Past|VerbForm=Fin', '16.34', 'VERB')...] ...,
    src_prons -> {16: [[('it', '16.37', 'nsubj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs',
    '16.38','PRON')], ...], ...}
    """

    alignment_points_verbs = {}

    for sent_id in info_src:
        aligned_sentence = alig_info[sent_id]
        for verb in info_src[sent_id]:
            position_v = int(re.findall(r'(?<=\.)\d+', verb[1])[0]) - 1
            # look for position in alignments
            align_points = find_alignment_points(aligned_sentence, position_v)
            if sent_id in alignment_points_verbs:
                alignment_points_verbs[sent_id].append(align_points)
            else:
                alignment_points_verbs[sent_id] = [align_points]
    return alignment_points_verbs


def identify_targets(parsed_sentences, alignment_points):
    """
    :param parsed_sentences: {11: [(token, position, deprel, morph, head, postag), ...], ...}
    :param alignment_points_verbs: 11 [[19], [29]]
    :      alignment_points_prons: 11 [[[15]], [[27]]]
    """

    d_targets = {}

    for sent in alignment_points:
        all_targets = []
        for item in alignment_points[sent]:
            targets = []
            for point in item:
                # prons
                if isinstance(point, list):
                    t_prons = []
                    for p in point:
                        if p < len(parsed_sentences[sent]):
                            t_prons.append(parsed_sentences[sent][p])
                    targets.append(t_prons)
                # verbs
                else:
                    if point < len(parsed_sentences[sent]):
                        targets.append(parsed_sentences[sent][point])
            all_targets.append(targets)
        d_targets[sent] = all_targets
    return d_targets



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


def attached_prons_target(parsed_sentence, verb_position):

    for word in parsed_sentence:
        head = word[4]
        postag = word[5]
        if head == verb_position:
            if postag == "PRON":
                return word
    return False


def check_target_pronouns(verbs, prons, parse):
    """
    { 190: [([('temps', '196.7', 'nmod', 'Gender=Masc|Number=Sing', '196.2', 'NOUN')],
     [[('même', '196.6', 'amod', 'Gender=Masc|Number=Sing', '196.7', 'ADJ')]])], ...}
    """
    #
    improved = {} # sent_id : [((verb), (pron))]

    for sent_id in prons:
        oked = [False]*len(prons[sent_id])

        for i in range(len(prons[sent_id])):
            for pron_list in prons[sent_id][i]:
                for word in pron_list:
                    # if pronoun then ok
                    if word[5] == "PRON":
                        oked[i] = word
                    # else check is verb and check verb's children
                    # todo: how do i know which target child corresponds to which source child?
                    # todo: what I could do is look in a window of -1,+1 word, or something similar
                    # else:
                    #     for v_word in verbs[sent_id][i]:
                    #         if v_word[5] in ["VERB", "ADJ"]:
                    #             position = v_word[1]
                    #             child = attached_prons_target(parse[sent_id], position)
                    #             oked[i] = child
        improved[sent_id] = oked
    return improved


def classify_instances(source_instances, checked_instances):
    """
    source_instances -> [[('It','7.1','nsubj','Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs','7.2','PRON')],
    [('it', '7.19', 'obj', 'Case=Acc|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '7.18', 'PRON')]] 2

    checked_instances -> [False, False]
    """
    pleonastic, nominals, non_nominals = {}, {}, {}

    for sent in source_instances:
        for i in range(len(source_instances[sent])):
            for word in source_instances[sent][i]:
                deprel = word[2]
                # expletives
                if "expl" in deprel:
                    tword = checked_instances[sent][i]
                    if tword:
                        token = tword[0]
                        if token.lower() in ["il"]:
                            if sent in pleonastic:
                                pleonastic[sent].append(word)
                            else:
                                pleonastic[sent] = [word]
                else:
                    # != False
                    tword = checked_instances[sent][i]
                    if tword:
                        token = tword[0]
                        # events
                        if token.lower() in ["cela", "ça", "ceci"]:
                            if sent in non_nominals:
                                non_nominals[sent].append(word)
                            else:
                                non_nominals[sent] = [word]
                        # nominals
                        if token.lower() in ["il", "elle", "le", "la", "l'"]:
                            if sent in nominals:
                                nominals[sent].append(word)
                            else:
                                nominals[sent] = [word]

    return pleonastic, nominals, non_nominals


def group_multiples(d_pleo, d_nom, d_non_nom):

    # {57: [('it', '58.6', 'obl', 'Case=Acc|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '58.4', 'PRON')],
    # 256: [('it', '310.4', 'nsubj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '310.7', 'PRON')]}

    multiples = {}

    for key in d_pleo:
        for pron in d_pleo[key]:
            position = pron[1]
            if key in multiples:
                multiples[key].append((position, "pleonastic_ref"))
            else:
                multiples[key] = [(position, "pleonastic_ref")]

    for key in d_nom:
        for pron in d_nom[key]:
            position = pron[1]
            if key in multiples:
                multiples[key].append((position, "nominal_ref"))
            else:
                multiples[key] = [(position, "nominal_ref")]

    for key in d_non_nom:
        for pron in d_non_nom[key]:
            position = pron[1]
            if key in multiples:
                multiples[key].append((position, "non_nominal_ref"))
            else:
                multiples[key] = [(position, "non_nominal_ref")]
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

