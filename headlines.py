# HEADLINES.PY
#!/usr/bin/env python

import sys
import nltk
import os
import os.path
import random

from nltk.stem.wordnet import WordNetLemmatizer


def generateHeadline(text):
    text = text.strip()
    # Load sentence tokenized for English
    tokenizer = nltk.data.load('nltk:tokenizers/punkt/english.pickle')

    # Tokenize text into sentences
    sentences = tokenizer.tokenize(text)

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
        
    
    for main_root, dirs, files in os.walk(doc_dir):
        dirs.sort()        
        for d in dirs:
            for root, _, files in os.walk(os.path.join(main_root, d)):
                files.sort()   
                if not pickAll:
                    if pickRandom:
                        files = random.sample(files, 1)
                    else:
                        files = [files[0]]
                for f in files:
                    if f[0] == '.':
                        continue
                    fullpath = os.path.join(root, f)
                    in_file = open(fullpath, "r")
                    text = in_file.read()
                    in_file.close()
                    print "Generating headline for: " + fullpath
                    headline = generateHeadline(text)
                    out_file = open(out_dir + f, "w")
                    out_file.write(headline)
                    out_file.close()