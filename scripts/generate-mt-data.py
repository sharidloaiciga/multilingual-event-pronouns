#! /usr/bin/env python3
# -*- encoding: utf-8 -*-

import functions as f
import sys
import logging

def main():

    if len(sys.argv) != 5:

        sys.stderr.write("Usage: {} {} {} {} {} \n".format(sys.argv[0], "src_parses_dir", "tgt_parses_dir",
                                                           "bitext_file", "alignment_file"))
        sys.exit(1)

    logging.basicConfig(filename='DEBUG_generate-mt-data_.log', level=logging.DEBUG)
    logging.info('Main started')

    src_parse_dir = sys.argv[1]
    tgt_parse_dir = sys.argv[2]
    bitext_key_file = sys.argv[3]
    data_alignment = sys.argv[4]

    document_links, sentence_links = f.read_bitext_correspondances(bitext_key_file)

    print("number of original en-fr documents:", len(document_links))

    alignments_enfr = f.read_word_alignments(data_alignment, sentence_links)

    files = sorted(document_links.keys())

    # if a document is not in bitext.xml, it shouldn't be included in the word alignment files.
    for src_file in files:

        # alignments
        alignments = alignments_enfr[src_file]

        # get parsed data
        tgt_file = document_links[src_file]
        tgt_parses = f.get_parsing(tgt_parse_dir + tgt_file)
        src_parses = f.get_parsing(src_parse_dir + src_file)

        # adjust sentence correspondence between documents
        adjusted_src, adjusted_tgt = f.adjust_documents(src_parses, tgt_parses, sentence_links[src_file])

        # identify source verbs & it pronouns
        src_verbs, src_prons = f.identify_src_verbs_prons(adjusted_src)

        # identify alignment points for previous verbs & pronouns
        # example { 16: [([2], [[2]])],...}

        # get alignment points
        align_points_verbs = f.identify_verbs_alignment_points(src_verbs, alignments)
        align_points_prons = f.identify_prons_alignment_points(src_prons, alignments)

        # get target words correspoding to the alignment points

        tgt_verbs = f.identify_targets(adjusted_tgt, align_points_verbs)
        tgt_prons = f.identify_targets(adjusted_tgt, align_points_prons)

        # todo: at this point I have the aligned pronouns to the source pronouns, but I'll use the verbs
        # todo: difference in performance if one or the other?

        # improve the pronoun alignments by using target verb info
        checked_prons = f.check_target_pronouns(tgt_verbs, tgt_prons, adjusted_tgt)

        # get another language to filter original examples

        pleo, nom, event = f.classify_instances(src_prons, checked_prons)

        # for key in adjusted_src:
        #     print("english sentence ====> ")
        #     sentence = []
        #     for x in adjusted_src[key]:
        #         sentence.append(x[0])
        #     print(sentence)
        #     print("french sentence ====> ")
        #     sentence = []
        #     for x in adjusted_tgt[key]:
        #         sentence.append(x[0])
        #     print(sentence)
        #
        #     if key in src_prons:
        #         print("src_prons ----------->")
        #         print(src_prons[key])
        #
        #         print("tgt_prons ----------->")
        #         print(tgt_prons[key])
        #
        #         print("align_points_prons ----------->")
        #         print(align_points_prons[key])
        #
        #         print("tgt_verbs ----------->")
        #         print(tgt_verbs[key])
        #
        #         print( "align_points_verbs ----------->")
        #         print(align_points_verbs[key])
        #
        #     print("\n")
        #     if key in pleo:
        #         print("pleonastic -----> ")
        #         print(pleo[key])
        #     if key in nom:
        #         print("nominal_ref -----> ")
        #         print(nom[key])
        #     if key in event:
        #         print("non_nominal -----> ")
        #         print(event[key])
        #     print("\n")
        #
        # print("end of document ----------------------")

        # format sentence and write document out

        f_new = open("/Users/xloish/PycharmProjects/abstract_coref/data_sharid/it-disamb/mt/2ndround/en-fr/" +
                    src_file + ".conll12_format", "w", encoding="utf-8")
        first_line = "#begin document " + src_file + ";" + "\n" + "\n"
        f_new.write(first_line)

        formated_doc = f.format_doc(src_file, adjusted_src, pleo, nom, event)

        for s in formated_doc:
            for w in formated_doc[s]:
                f_new.write(w + "\n")
            f_new.write("\n")
        f_new.write("#end document;" + "\n")
        f_new.close()

if __name__ == "__main__":
    main()
