import os
from nltk.tree import *
import re


def compressSentence(sentence, byte_limit):
    print '== COMPRESSING =='
    sentence = sentence.replace("\n", "")
    outfile = open('headline.tmpdata', 'w')
    outfile.write(sentence)
    outfile.close()

    parser_out = os.popen("lexparser.sh headline.tmpdata").readlines()

    stripper_out = [i.strip() for i in parser_out if len(i.strip()) > 0]
    tree_string = " ".join([i for i in stripper_out if i[0] == "("])

    if not len(tree_string):
        return None

    #print tree_string

    t = ParentedTree.parse(tree_string)  # create Tree structure
    # CLAUSE LEVEL
    # SBAR: relative claused and subordinate clauses, including indirect questions
    # PHRASE LEVEL
    # PP: Prepositional phrase. Phrasal headed by a preposition
    timetags = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                'saturday', 'sunday', 'yesterday', 'tomorrow']
    announcetags = ['said', 'announced', 'hoped', 'reported']

    allLeaves = t.pos()
    can_prune = True  # assume I can prune at first iteration

    # FIRST STEP: principal tree structure
    # Want to detect if there is a main clouse or just coordination.
    # If a main clouse is available, want to know if it introduces an indirect speech
    mainPhrase = False
    indirectSpeech = False
    coordinator = False
    for sub in t.subtrees(filter=lambda x: len(x.treeposition()) == 2 and x.parent().node == 'S'):
        if sub.node == 'CC':
            coordinator = True
        if sub.node == 'VP':
            mainPhrase = True
            if listIntersect(sub.leaves(), announcetags):
                # IDEA: can also exploit ration of lenght?
                indirectSpeech = True
    if mainPhrase and indirectSpeech:
        print 'Detected indirect speech'
        for sub in t.subtrees(filter=lambda x: len(x.treeposition()) == 2 and x.node == 'S'):
            t = ParentedTree('(ROOT ' + sub.pprint() + ')')
            indirectSpeech = False
            allLeaves = t.pos()  # get new nodes
            sentence = sentenceFromNodes(allLeaves)
            break

    if coordinator and not mainPhrase:
        print 'No main phrase'
        for sub in t.subtrees(filter=lambda x: len(x.treeposition()) == 2 and x.node == 'S'):
            t = ParentedTree('(ROOT ' + sub.pprint() + ')')
            mainPhrase = True
            allLeaves = t.pos()  # get new nodes
            sentence = sentenceFromNodes(allLeaves)
            break

    # SECOND STEP: iterative pruning
    while (len(sentence) > byte_limit and can_prune):

        candidates = []  # candidates phrases for removal

        for sub in t.subtrees(filter=lambda x: len(x.leaves()) and x.leaves()[0].lower() != 'to' and
                              ((x.node == 'PP' and x[0].node != 'TO')
                              or (x.node == 'JJ')
                              or (x.node == 'SBAR' and not listIntersect(x.parent().leaves(), announcetags) and
                                  (x.left_sibling() is None or (x.left_sibling().node != 'VBG')))
                              or (x.node == 'S' and (x.left_sibling() is None or (x.left_sibling().node != 'VBG' and x.left_sibling().node != 'IN')))
                              or (x.node == 'NP' and sentenceFromNodes(x.pos()).lower() in timetags))):

            if (sub.node == 'SBAR'):
                if listIntersect(sub.parent().leaves(), announcetags):
                    print 'Ignoring SBAR related to transitive verb'
                    continue

            if (sub.node == 'S' and sub.parent().node == 'SBAR'):
                if listIntersect(sub.parent().parent().leaves(), announcetags):
                    print 'Ignoring S related to transitive verb'
                    continue

            # and (x.parent().node == 'S' or x.parent().node == 'VP')
            leaves = sub.pos()
            lenLeaves = sum(len(s[0]) for s in leaves) + len([l for l in leaves if l[0] not in "\".,;:?''``"])

            # ======== Adjust penalty ==========

            # Add penalty according to depth in the parsing tree
            penalty = min(0, 30 - 0.1 * (len(sub.treeposition()) - 1) * lenLeaves)

            # Preserve adjectives if possible
            if sub.node == 'JJ':
                penalty += max(0, 200 - 20 * (len(sub.treeposition()) - 1))  # want to keep adjectives
                print 'Adjective - penalty: ' + str(penalty)

            # Time tag: remove now!
            if sub.node == 'NP':
                penalty = -lenLeaves

            # Penalty for Proper Nouns (want to keep)
            penalty += 5 * len([l for l in sub.pos() if l[1] == 'NNP'])

            # Do not remove if we loose too much of the sentence
            if len(sentence) < 1.2 * byte_limit and len(sentence) - lenLeaves < 0.8 * byte_limit:
                lenLeaves = - 10e15  # do not remove!
                print 'Marginal condition for removal not matched'

            # Do not remove main phrase
            if sub.parent().node == 'ROOT':
                lenLeaves = -10e15  # do not remove!

            # ================================================================

            # Append to candidates
            if lenLeaves > 0:
                candidates.append((sub.node, lenLeaves + penalty, leaves))

        print 'These are the candidates: '
        print candidates

        if (len(candidates) == 0):
            can_prune = False  # finished. Nothing to remove
        else:
            # Decide which candidate to remove
            # Sort by len
            candidates.sort(key=lambda tup: tup[1])
            toRemove = candidates[0]  # pick shortest one

            # Remove from tree
            leavesIdxs = find_sub_list(toRemove[2], allLeaves)
            tpos = t.treeposition_spanning_leaves(leavesIdxs[0], 1 + leavesIdxs[1])
            del t[tpos]

            allLeaves = t.pos()  # get new nodes
            sentence = sentenceFromNodes(allLeaves)

            print bcolors.WARNING + "-->  (" + str(len(sentence)) + ") " + sentence + bcolors.ENDC
    return sentence


def listIntersect(main, l):
    return len([x for x in main if x in l])


def find_sub_list(sl, l):
    sll = len(sl)
    for ind in (i for i, e in enumerate(l) if e == sl[0]):
        if l[ind:ind + sll] == sl:
            return ind, ind + sll - 1


def sentenceFromNodes(allLeaves):
    if not len(allLeaves):
        return ''
    r = " ".join([i[0] for i in allLeaves])
    r = r.replace(' ,', ',')
    r = r.replace(' .', '.')
    r = r.replace(' ;', ';')
    r = r.replace(' !', '!')
    r = r.replace(' ?', '?')
    r = r.replace('( ', '(')
    r = r.replace(' )', ')')
    r = r.replace(' "', '"')
    r = r.replace(" ''", "''")
    r = r.replace(" '", "'")

    r = re.sub(r'([,;.]*)\.', r[-1], r)  # fix multiple punctuation keeping last symbol
    r = r.strip()
    r = r[0].upper() + r[1:]

    return r


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
