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

from gensim import corpora
from gensim.models import ldamodel

from compress import compressSentence


## Settings
# Consider the entire doc set to generate a single headline
useDocsetData = True

# Lemmatize words before computing frequency
useLemmasForFrequency = True


# text: article to analyze
# docset: list of texts of all articles in the docset
def generateHeadline(text, docset):
    # LOAD LIBRARIES AND DATASETS
    # Load sentence and word tokenizers for English
    sent_tokenizer = nltk.data.load('nltk:tokenizers/punkt/english.pickle')
    word_tokenizer = TreebankWordTokenizer()
    wnl = WordNetLemmatizer()
    stopwords = st.words()  # get list of 2431 stopwords from NLTK corpus
    docsetText = "/n".join(docset)

    # PREPROCESSING
    text = text.strip()

    # Words frequency
    lowercase_words = [w.lower()
                       for w in word_tokenizer.tokenize(docsetText if useDocsetData else text)]

    all_sentences = sent_tokenizer.tokenize(docsetText)

    useful_words = [w for w in lowercase_words if w not in stopwords and len(w) > 2]

    if useLemmasForFrequency:
        useful_words = [wnl.lemmatize(w) for w in useful_words]
    input_to_dictionary = [[wnl.lemmatize(w) for w in word_tokenizer.tokenize(sentence)
                           if w.lower() not in stopwords and len(w) > 2] for sentence in all_sentences]
    #print input_to_dictionary
    #sys.exit(0)
    dictionary = corpora.Dictionary(input_to_dictionary)
    #print dictionary
    corpus = [dictionary.doc2bow(i) for i in input_to_dictionary]
    #print corpus
    lda = ldamodel.LdaModel(corpus, id2word=dictionary, num_topics=1)
    most_frequent_words = [a[1] for a in lda.show_topics(formatted=False)[0]]
    #print most_frequent_words
    #sys.exit(0)
    #corpus =
    word_freq = FreqDist(useful_words)
    sentences = sent_tokenizer.tokenize(text)

    working_sentences = [sentence.lower() for sentence in sentences]

    result = ''
    max_words = -1
    for s in working_sentences:
        count = 0
        for word in most_frequent_words:
            if word in s:
                count = count + 1
        if count > max_words:
            result = s
            max_words = count
            break


    result = compressSentence(result, 76, word_freq)
    return result


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
                docset = []  # read and store the entire docset for processing purposes
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
                    #sys.exit(0)
                    if headline is not None and len(headline):
                        out_file = open(out_dir + files[i], "w")
                        out_file.write(headline)
                        out_file.close()
                    else:
                        print "ERROR: headline result was empty!"

                print ''
