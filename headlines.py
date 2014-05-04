# HEADLINES.PY
#!/usr/bin/env python

import sys
import nltk
import os
import os.path

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
    if len(sys.argv) != 3:
        print "Requires 2 arguments <documents_dir> <output_dir>"
        sys.exit(0)

    doc_dir = sys.argv[1]
    out_dir = sys.argv[2]
    for root, _, files in os.walk(doc_dir):
        for f in files:
            fullpath = os.path.join(root, f)
            in_file = open(fullpath, "r")
            text = in_file.read()
            in_file.close()
            print "Generating headline for: " + fullpath
            headline = generateHeadline(text)
            out_file = open(out_dir + f, "w")
            out_file.write(headline)
            out_file.close()
