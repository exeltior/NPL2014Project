# HEADLINES.PY
#!/usr/bin/env python

import sys
import re
import nltk
import os, os.path

def generateHeadline(text):
    return text

if __name__ == "__main__": 
   if len(sys.argv) != 3:
      print "This programs extract models"
      print "Requires 2 arguments <model_dir> <output_dir>"
      sys.exit(0)
      
   doc_dir = sys.argv[1]
   out_dir = sys.argv[2]
  
   last_docset = "";
   count = 0;
   
   for root, _, files in os.walk(doc_dir):
       for f in files:
           docset = f.split(".")[0]
           if (last_docset != docset):
               count = 0
               last_docset = docset
               
           fullpath = os.path.join(root, f)
           in_file = open(fullpath,"r")
           text = in_file.read()
           in_file.close()               
            
           out_file = open(out_dir+docset.upper()+"."+str(count)+".txt","w")
           out_file.write(text)
           out_file.close()  
           count = count+1
