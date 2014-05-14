# HEADLINES.PY
#!/usr/bin/env python

import sys
import nltk
import os
import os.path
import random

from nltk.tokenize import *
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords as st
from nltk.probability import FreqDist

from compress import compressSentence


## Settings
# Consider the entire doc set to generate a single headline
useDocsetData = True; 

# Lemmatize words before computing frequency
useLemmasForFrequency = True;

# text: article to analyze
# docset: list of texts of all articles in the docset
def generateHeadline(text, docset):
    
    # LOAD LIBRARIES AND DATASETS
    # Load sentence and word tokenizers for English
    sent_tokenizer = nltk.data.load('nltk:tokenizers/punkt/english.pickle')  
    word_tokenizer = TreebankWordTokenizer()
    wnl = WordNetLemmatizer()    
    stopwords = st.words() # get list of 2431 stopwords from NLTK corpus
    docsetText = "/n".join(docset)
    
    # PREPROCESSING
    text = text.strip()

    
    # Words frequency
    lowercase_words = [w.lower()
                        for w in word_tokenizer.tokenize(docsetText if useDocsetData else text)] 
    
    useful_words = [w for w in lowercase_words 
                    if (w not in stopwords and len(w) > 2)]    
    
    if useLemmasForFrequency:
        useful_words = [wnl.lemmatize(w) for w in useful_words]
    
    word_freq = FreqDist(useful_words)
    
    
    # Tokenize text into sentences
    sentences = sent_tokenizer.tokenize(text)
    
    ## Attemp to give a score to find the best sentence. But is seems than in
    ## fast the best sentence is always the first one
    
    # Give a score to each sentence
    #scores = np.zeros(len(sentences))
    #for idx in xrange(len(sentences)):
        #sentence = sentences[idx]
        #words = [w.lower() for w in word_tokenizer.tokenize(sentence)]
        #words = [w for w in words if (w not in stopwords and len(w) > 2)]
        #for w in words:
            #if useLemmasForFrequency:
                #w = wnl.lemmatize(w)
            #scores[idx] += word_freq.freq(w)
        #if scores[idx] > 0:
            #scores[idx] /=  len(words) 
            
    #scores[0] += 0.005
        
    #idx_max = scores.argmax()
    #print "Best sentence " + str(idx_max) + " -> score: " + str(scores[idx_max])
    #print sentences[idx_max]
            
        
        

    # Consider only first sentence
    first = sentences[0]

    # Tokenize and POS tag on the first sentence
    tokens = nltk.word_tokenize(first)
    pos = nltk.pos_tag(tokens)
    # OPTIONAL: lemmatization
    wnl = WordNetLemmatizer()
    lemmas = {}
    for w in tokens:
        lemmas[w] = wnl.lemmatize(w)
    # Remove closed class words
    result = ""
    openclassTags = ('V', 'NN', 'JJ')
    for word, postag in pos:
        if postag.startswith(openclassTags):
            result += word
            result += ' '
     
    compressed = compressSentence(first, 75)    
    return first



    

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Requires 2 arguments <documents_dir> <output_dir>"
        print "Usage headlines.py <documents_dir> <output_dir> [--all|random]"
        print "Use --all to produce headline for ALL the documents in each docset, --random to pick one at random, default picks the first one"
        sys.exit(0)

    doc_dir = sys.argv[1]
    out_dir = sys.argv[2]
    pickAll = '--all' in sys.argv
    if not pickAll:
        pickRandom = '--random' in sys.argv
        
    # Clean out dir
    print "Cleaning peers directory..."
    for main_root, dirs, files in os.walk(out_dir):
        for f in files:
            os.remove(out_dir + f)    
        
    
    for main_root, dirs, files in os.walk(doc_dir):
        dirs.sort()        
        for d in dirs:
            for root, _, files in os.walk(os.path.join(main_root, d)):
                files.sort()  
                docset = [] # read and store the entire docset for processing purposes
                for f in files:
                    if f[0] == '.':
                        continue
                    fullpath = os.path.join(root, f)
                    in_file = open(fullpath, "r")
                    text = in_file.read()
                    in_file.close()
                    docset.append(text)
                    
                if pickAll:
                    idxs = range(len(docset))
                else:
                    if pickRandom:
                        idxs = random.sample(range(len(docset)), 1)
                    else:
                        idxs = [0]                      
                
                for i in idxs:
                    fullpath = os.path.join(root, files[i])
                    print "Generating headline for: " + fullpath
                    headline = generateHeadline(docset[i], docset)
                    if headline != None and len(headline):
                        out_file = open(out_dir + files[i], "w")
                        out_file.write(headline)
                        out_file.close()    
                    else:
                        print "ERROR: headline result was empty!"
                print ''