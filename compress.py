import nltk
import os
from nltk.tree import *
import numpy as np
import re


def compressSentence(sentence, byte_limit):
    print '== COMPRESSING =='
    outfile = open('headline.tmpdata', 'w')
    outfile.write(sentence)
    outfile.close()

    parser_out = os.popen("lexparser.sh headline.tmpdata").readlines()
    
    stripper_out = [i.strip() for i in parser_out if len(i.strip())>0]
    tree_string = " ".join( [i for i in stripper_out if i[0] == "("] )
    
    #print tree_string
        
    t = ParentedTree.parse(tree_string) # create Tree structure
    # CLAUSE LEVEL
    # SBAR: relative claused and subordinate clauses, including indirect questions
    # PHRASE LEVEL
    # PP: Prepositional phrase. Phrasal headed by a preposition
    timetags = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                'saturday', 'sunday', 'yesterday', 'tomorrow']
    
    result = sentence # start with the full sentence and loop to remove elements
    allLeaves = t.pos()    
    can_prune = True # assume I can prune at first iteration
    
    while (len(sentence) > byte_limit and can_prune == True):        
                
        candidates = [] # candidates phrases for removal
        for sub in t.subtrees(filter=lambda x: 
                              (x.node == 'PP' and x[0].node != 'TO') 
                              or x.node == 'JJ'
                              or x.node == 'SBAR' and (x.left_sibling() == None or x.left_sibling().node != 'VBG')
                              or x.node == 'S' and x.parent().node == 'S'
                              or x.node == 'NP' and sentenceFromNodes(x.pos()).lower() in timetags):
            penalty = 0
            if sub.node == 'JJ':
                penalty = 100;
            
            leaves = sub.pos();
            lenLeaves = sum(len(s[0]) for s in leaves) + len([l for l in leaves if l[0] not in "\".,;:?''``"])
            if lenLeaves:     
                candidates.append((sub.node, lenLeaves+penalty, leaves))
        
        #print 'These are the candidates: '
        #print candidates
        
        if (len(candidates) == 0):
            can_prune = False # finished. Nothing to remove
        else:
            # Decide which candidate to remove
            # Sort by len
            candidates.sort(key=lambda tup: tup[1])
            toRemove = candidates[0] # pick shortest one
            
            # Remove from tree
            leavesIdxs = find_sub_list(toRemove[2], allLeaves)
            tpos = t.treeposition_spanning_leaves(leavesIdxs[0], 1+leavesIdxs[1]) 
            del t[tpos]
            
            allLeaves = t.pos() # get new nodes            
            sentence = sentenceFromNodes(allLeaves)
            
            print "-->  (" + str(len(sentence)) + ") " + sentence    
    return sentence   

def find_sub_list(sl,l):
    sll=len(sl)
    for ind in (i for i,e in enumerate(l) if e==sl[0]):
        if l[ind:ind+sll]==sl:
            return ind,ind+sll-1
        
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
    
    r = re.sub(r'([,;.]*)\.', r[-1], r) #fix multiple punctuation keeping last symbol
    r = r.strip()
    r = r[0].upper() + r[1:]
    
    return r