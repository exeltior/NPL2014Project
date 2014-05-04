# HEADLINES.PY
#!/usr/bin/env python

import sys
import re
import nltk
import os, os.path


# Copy docs from 
if __name__ == "__main__": 
    if len(sys.argv) != 3:
        print "This programs extract plain text from DUC documents"
        print "Requires 2 arguments <documents_dir> <output_dir>"
        sys.exit(0)
      
    doc_dir = sys.argv[1]
    out_dir = sys.argv[2]


    for root, _, files in os.walk(doc_dir):        
        for f in files:
            if f[0] == '.':
                continue
            
            docset = root.split("/")[-1]
    
            fullpath = os.path.join(root, f)
            in_file = open(fullpath,"r")
            text = in_file.read()
            in_file.close()               
            startString = '<TEXT>'
            endString = '</TEXT>'
            text = text[text.find(startString)+len(startString):text.find(endString)]               
            text = text.strip()
            
            current_out_path = out_dir + docset + '/'
            if not os.path.exists(current_out_path):
                os.makedirs(current_out_path)            
            
            out_file = open(current_out_path + docset +"." + f + ".txt","w")
            out_file.write(text)
            out_file.close()         
