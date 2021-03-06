import os
from nltk.tree import *
import re
from nltk.stem.wordnet import WordNetLemmatizer
from freebase import compressEntityName

entities = {}
timetags = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
            'saturday', 'sunday', 'yesterday', 'tomorrow']
announcetags = ['said', 'say', 'says', 'announced', 'announce', 'announces',
                'hoped', 'hope', 'hopes', 'reported', 'report', 'reports',
                'found', 'revealed', 'decided']

def returnCompressionDict():
    return entities

def compressSentence(sentence, byte_limit, w_freq):
    print '== COMPRESSING =='
    print w_freq
    wnl = WordNetLemmatizer()
    #entities.clear()
    
    
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


    allLeaves = t.pos()
    can_prune = True  # assume I can prune at first iteration

    # FIRST STEP: principal tree structure
    # Want to detect if there is a main clouse or just coordination.
    # If a main clouse is available, want to know if it introduces an indirect speech
    mainPhrase = False
    indirectSpeech = False #form 'The price will growth soon, John said'
    coordinator = False
    
    for sub in t.subtrees(filter=lambda x: len(x.treeposition()) == 2 and x.parent().node == 'S'):
        if sub.node == 'CC':
            coordinator = True
        if sub.node == 'VP':
            mainPhrase = True
            if listIntersect(t.leaves()[-4:] , announcetags): # [-4:0] looking for an annoutce tag toward the end
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
    

    # Entity compression
    for sub in t.subtrees(filter=lambda x: x.node == 'NP' and x.height() in range(3,5)):
        if sum(i[1] == 'NNP' for i in sub.pos()) >= 2:
            entityString = sentenceFromNodes(findLongestNNPSequence(sub.pos()))
            if entityString not in entities:
                newEntity = None
                print sub.pos()
                try:
                    newEntity = compressEntityName(entityString)
                    if newEntity and len(newEntity) and newEntity != entityString:
                        entities[entityString] = newEntity
                    else:
                        entities[entityString] = None                    
                except:
                    print bcolors.FAIL + "Entity compression exception for: " + entityString + bcolors.ENDC
                

                    
                

    # SECOND STEP: iterative pruning
    while (len(sentence) > byte_limit and can_prune):

        candidates = []  # candidates phrases for removal

        for sub in t.subtrees(filter=lambda x: 
                              (x.node == 'PP') or
                              (x.node == 'JJ') or
                              (x.node == 'SBAR') or #and not listIntersect(x.parent().leaves(), announcetags))
                              (x.node == 'S') or
                              ((x.node == 'NP' or x.node == 'NNP') and sentenceFromNodes(x.pos()).lower() in timetags)):
            
            leaves = sub.pos()
            lenLeaves = sum(len(s[0]) for s in leaves) + len([l for l in leaves if l[0] not in "\".,;:?''``"]) 
            
            # Do not remove main phrase
            if sub.parent().node == 'ROOT':
                continue   
            
            # Do not remove if we loose too much of the sentence
            #if (len(sentence) < 1.2 * byte_limit and len(sentence) - lenLeaves < 0.8 * byte_limit) or len(sentence) - lenLeaves < 0.5 * byte_limit:
                #continue
            
            if sub.node == 'JJ' and lenLeaves < 6:
                continue
            
            # Do not remove if first leaf is TO after a verb
            if (sub.node == 'SBAR' or sub.node == 'S'):
                if len(sub.pos()):
                    idxs = find_sub_list(sub.pos(), allLeaves)
                    if idxs[0] > 0:
                        if (allLeaves[idxs[0]-1][1].startswith('TO')):
                            continue            
            
            
            # Condition on adjectives. Do not remove if they follow a verb
            if (sub.node == 'JJ' and len(sub.pos())):
                idxs = find_sub_list(sub.pos(), allLeaves)
                if idxs[0] > 0:
                    if (allLeaves[idxs[0]-1][1].startswith('VB')):
                        continue
                
            
            # Condition on S and SBAR: should have at least 1 sibling that is no VBG or IN
            if (sub.node == 'S' or sub.node == 'SBAR'):
                if not sub.right_sibling() and not sub.left_sibling():
                        continue
                if sub.left_sibling() and (sub.left_sibling().node == 'VBG' or sub.left_sibling().node == 'IN'):
                        continue
                
            # Ignore SBAR that support a verb like 'said that...'
            if (sub.node == 'SBAR'):
                if listIntersect(sub.parent().leaves(), announcetags):
                    print 'Ignoring SBAR related to transitive verb'
                    continue
                
            # Remove coordination together with second part of the phrase
            if (sub.node == 'S'):
                if sub.left_sibling() and sub.left_sibling().node == 'CC':
                    leaves = sub.left_sibling().pos() + leaves
            
            #
            #if (sub.node == 'S' and sub.parent().node == 'SBAR'):
                #if listIntersect(sub.parent().parent().leaves(), announcetags):
                    #print 'Ignoring S related to transitive verb'
                    #continue


            # ======== Adjust penalty ==========

            # Add penalty according to depth in the parsing tree
            penalty = min(0, 30 - 0.1 * (len(sub.treeposition()) - 1) * lenLeaves)

            # Preserve adjectives if possible
            if sub.node == 'JJ':
                penalty += max(0, 300 - 20 * (len(sub.treeposition()) - 1))  # want to keep adjectives
                print 'Adjective - penalty: ' + str(penalty)

            # Time tag: remove now!
            if sub.node == 'NP' or sub.node == 'NNP': 
                # note implicit condition of time tag found in the leaves
                penalty = -lenLeaves

            # Penalty for Proper Nouns (want to keep)
            # penalty += 5 * len([l for l in sub.pos() if l[1] == 'NNP'])


                
            # Penalty according to most common words
            p = 0;
            for i in leaves:
                ww = i[0].lower()
                if ww not in announcetags:
                    ww = wnl.lemmatize(i[0].lower())
                    p +=  w_freq[ww] ** 2
            penalty += p
            print "Penalty word frequency: " + str(p)

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
    
    if len(sentence) < 1.1*byte_limit:
        while len(sentence) < 1.2*byte_limit:
            pass
        
    return sentence

def findLongestNNPSequence(l):
    result = []
    temp = []
    for e in l:
        if e[1] == 'NNP':
            temp.append(e)
        else:
            if len(temp) >= len(result):
                result = temp[:]
                temp = []
    if len(temp) >= len(result):
        result = temp[:]
        temp = []    
    return result

def findLongestNSequence(l):
    result = []
    temp = []
    for e in l:
        if e[1].startswith('N'):
            temp.append(e)
    return temp



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
    r = r.replace('-LRB- ', '(')
    r = r.replace(' -RRB-', ')')
    
    r = re.sub(r'([,;.]+)\.', '.', r) #fix multiple punctuation keeping last symbol
    r = re.sub(r'^[^\w]*', '', r)
    r = r.strip()

    for key in sorted(entities, key=len, reverse=True):
        if entities[key]:
            r = r.replace(key, entities[key]) 
        
    for tag in timetags:
        r = re.sub(r'(?i)'+tag, '', r)
    
    if len(r) > 1:
        r = r[0].upper() + r[1:]
    elif len(r):
        r = r[0].upper()
    
    return r


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
