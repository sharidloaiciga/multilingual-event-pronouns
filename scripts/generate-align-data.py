#! /usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import os
import re
import functions as f

"""
generate MT data with pronoun translations of a language in Europarl
"""


def identify_src_prons(parses):
    """
    {2: [('Although', '3.1', 'advmod', 'noMorph', '3.7', 'ADV'),
     (',', '3.2', 'punct', 'noMorph', '3.7', 'PUNCT'), ...], 3: [(), ()]}
    """
    srcProns = {}

    for key in sorted(parses.keys()):
        #if str(key) in list_sentences:
        for word in parses[key]:
            token = word[0]
            postag = word[5]
            if postag == "PRON" and token.lower() == "it":
                if key in srcProns:
                    srcProns[key].append(word)
                else:
                    srcProns[key] = [word]
    return srcProns


def identify_prons_alignment_points(src_prons, alig_info):
    """
    src_prons -> {16: [('It', '7.1', 'nsubj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '7.2', 'PRON'),
 ('it', '7.19', 'obj', 'Case=Acc|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '7.18', 'PRON')], ...}
    """
    import re

    alignment_points_prons = {}

    for sent_id in src_prons:
        aligned_sentence = alig_info[sent_id]
        align_points_found = []
        for pron in src_prons[sent_id]:
            position_p = int(re.findall(r'(?<=\.)\d+', pron[1])[0]) - 1
            # look for position in alignments
            align_points = f.find_alignment_points(aligned_sentence, position_p)
            align_points_found.append(align_points)
        alignment_points_prons[sent_id] = align_points_found
    return alignment_points_prons


def identify_targets(parsed_sentences, alignment_points):
    """
    :param parsed_sentences: {11: [(token, position, deprel, morph, head, postag), ...], ...}
    :param alignment_points_verbs: 11 [[19], [29]]
    """

    d_targets = {}
    for sent in alignment_points:
        all_targets = []
        for item in alignment_points[sent]:
            targets = []
            if item != []:
                for point in item:
                    if point < len(parsed_sentences[sent]):
                        targets.append(parsed_sentences[sent][point])
            else:
                targets.append("empty")
            all_targets.append(targets)
        d_targets[sent] = all_targets
    return d_targets


def guess_class(tgt_pron, deprel):

    if deprel == "expl" and tgt_pron != "empty":
        return "pleonastic_ref"
    if tgt_pron in ["cela", "ça", "ceci"]:
        return "event_ref"
    if tgt_pron in ["il", "elle", "le", "la", "l'"]:
        return "nominal_ref"

    return "unknown_ref"


def get_overlapping_files(data_dir):

    languages = os.listdir(data_dir)
    common_files = []
    for lang in languages:
        if os.path.isdir(data_dir + "/" + lang):
            current_files = os.listdir(data_dir + "/" + lang)
            if common_files:
                intersection_files = set.intersection(set(common_files), set(current_files))
                common_files = intersection_files
            else:
                common_files = current_files

    return common_files


# def get_ovelapping_sentences(parse_dir, align_dir):
#
#     languages = os.listdir(parse_dir)
#     round = {}
#
#     for lang in languages:
#         if lang != "en":
#             bitext_key_file = align_dir + "/en-" + lang + "/" + "bitext.xml"
#
#             with open(bitext_key_file, "r", encoding="utf-8") as f:
#                 soup = BeautifulSoup(f, "xml")
#                 # first language
#                 if round == {}:
#                     for doc_linking in soup.find_all("linkGrp"):
#                         src_doc = doc_linking["fromDoc"][3:-3] # "en/ep-00-01-17.xml.gz"
#                         current_sentences = []
#                         for link in doc_linking.find_all("link"):
#                             s_correspond = link["xtargets"].split(";") # ex:"36;36", "22 23;23", "38;38 39"
#                             src_sentence = s_correspond[0]
#                             current_sentences.append(src_sentence)
#
#                         round[src_doc] = current_sentences
#                 else:
#                     for doc_linking in soup.find_all("linkGrp"):
#                         src_doc = doc_linking["fromDoc"][3:-3] # "en/ep-00-01-17.xml.gz"
#                         current_sentences = []
#                         for link in doc_linking.find_all("link"):
#                             s_correspond = link["xtargets"].split(";") # ex:"36;36", "22 23;23", "38;38 39"
#                             src_sentence = s_correspond[0]
#                             current_sentences.append(src_sentence)
#
#                         if src_doc in round:
#                             previous = round[src_doc]
#                             overlapping_sentences = list(set.intersection(set(previous), set(current_sentences)))
#                             if overlapping_sentences:
#                                 round[src_doc] = overlapping_sentences
#                         else:
#                             round[src_doc] = current_sentences
#
#     return round


def print_sentence(parses, key, position):

    #[('Although', '3.1', 'advmod', 'noMorph', '3.7', 'ADV'),
    # (',', '3.2', 'punct', 'noMorph', '3.7', 'PUNCT'), ...]

    current = []
    previous_1 = []
    previous_2 = []
    if int(key)-2 in parses:
        for word in parses[int(key)-2]:
            previous_2.append(word[0])
    if int(key)-1 in parses:
        for word in parses[int(key)-1]:
            previous_1.append(word[0])
    for word in parses[key]:
        token_i = word[1]
        if token_i == position:
            current.append("__"+ word[0] +"__")
        else:
            current.append(word[0])

    all = " ".join(previous_2 + previous_1 + current)
    return all


def better(position, parse):

    window = range(position-3, position+3)
    sent_range = range(len(parse))
    for i in window:
        if i in sent_range:
            POS_token = parse[i][5]
            if POS_token == "PRON":
                return parse[i]
    return False


def compensate_align(tgt_prons, parses):
    '''

    :param tgt_prons: [['empty']] or [[(',', '14.17', 'punct', 'noMorph', '14.22', 'PUNCT')], ['empty']]
    :return:
    '''

    new = {}

    for key in tgt_prons:
        trans = []
        for pron_list in tgt_prons[key]:
            new_list = []
            for word in pron_list:
                if word == "empty":
                    new_list.append(word)
                else:
                    postag = word[5]
                    position = int(re.findall(r'(?<=\.)\d+', word[1])[0]) - 1
                    if postag == "PRON":
                        new_list.append(word)
                    else:
                        alternative = better(position, parses[key])
                        if alternative:
                            new_list.append(alternative)
                        else:
                            new_list.append(word)
            trans.append(new_list)
        new[key] = trans
    return new



def main():

    if len(sys.argv) != 6:

        sys.stderr.write("Usage: {} {} {} {} {} {} \n".format(sys.argv[0], "parse_dir", "overlap_files_dir",
                                                           "align_dir", "src_lang", "tgt_lang"))
        sys.exit(1)

    # languages # es/ et/ fi/ fr/ hu/ it/ lv/ nl/ pl/ pt/ ro/ sk/ sl/ sv/ en/
    src_lang = sys.argv[4]
    tgt_lang = sys.argv[5]
    parse_dir = sys.argv[1]
    src_parse_dir = parse_dir + "/" + src_lang + "/"  # parsing files from Opus
    tgt_parse_dir = parse_dir + "/" + tgt_lang + "/"
    bitext_file = sys.argv[2] + "/" + src_lang + "-" + tgt_lang + ".xml" # bitexts (xml files from Opus)
    data_alignment = sys.argv[3] + "/" + src_lang + "-" + tgt_lang + "/model/" + "aligned.grow-diag-final-and"

    # current language pair
    document_links, sentence_links = f.read_bitext_correspondances(bitext_file)
    alignments_srctgt = f.read_word_alignments(data_alignment, sentence_links)
    files = document_links.keys()

    # all valid documents
    common_lang_files = get_overlapping_files(parse_dir)
    valid_documents = list(sorted(set.intersection(set(files), common_lang_files)))

    #for src_file in files:
    for src_file in valid_documents:

        # alignments
        alignments = alignments_srctgt[src_file]

        # get parsed data
        tgt_file = document_links[src_file]
        tgt_parses = f.get_parsing(tgt_parse_dir + tgt_file)
        src_parses = f.get_parsing(src_parse_dir + src_file)

        # adjust sentence correspondence between documents
        adjusted_src, adjusted_tgt = f.adjust_documents(src_parses, tgt_parses, sentence_links[src_file])

        # identify source it pronouns
        src_prons = identify_src_prons(adjusted_src)

        # get alignment points
        align_points_prons = identify_prons_alignment_points(src_prons, alignments)

        # get target words corresponding to the alignment points
        tgt_prons = identify_targets(adjusted_tgt, align_points_prons)

        # sliding window to compensate bad alignment
        better_tgt_prons = compensate_align(tgt_prons, adjusted_tgt)

        for key in src_prons:
            for i in range(len(src_prons[key])):
                # ('it', '4.12', 'obj', 'Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs', '4.11', 'PRON')
                src_pron_position = src_prons[key][i][1]
                src_pron_deprel = src_prons[key][i][2]
                src_pron = src_prons[key][i][0].lower()
                # [('fond', '4.13', 'conj', 'Gender=Masc|Number=Sing', '4.7', 'NOUN'),
                # ('de', '4.14', 'case', 'noMorph', '4.15', 'ADP')]
                temp = better_tgt_prons[key][i]

                # for manual annotation
                # text_target = print_sentence(adjusted_tgt, key, tgt_prons[key][i])

                tgt_pron = "empty"
                if not temp:
                    tgt_pron = "empty"
                elif temp[0] == "empty":
                    tgt_pron = "empty"
                else:
                    tgt_pron = temp[0][0].lower() # take the first in case of multiple alignment points

                    # for manual annotation
                    # text_target = print_sentence(adjusted_tgt, key, temp[0][1])
                # for manual annotation
                # text_sentence = print_sentence(adjusted_src, key, src_pron_position)

                if tgt_lang == "fr":
                    classification = guess_class(tgt_pron, src_pron_deprel)
                    print(src_file, "\t", key, "\t", src_pron_position, "\t", src_pron, "\t",
                          classification, "\t", tgt_pron)

                    # this is for the manual annotation
                    #print(src_file, "\t", text_sentence, "\t", text_target, "\t", key, "\t", src_pron_position, "\t", src_pron, "\t",
                    #      classification, "\t", tgt_pron)

                else:
                    print(src_file, "\t", key, "\t", src_pron_position, "\t", tgt_pron)


if __name__ == "__main__":
    main()


