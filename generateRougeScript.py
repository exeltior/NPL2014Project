# HEADLINES.PY
#!/usr/bin/env python

import sys
import re
import nltk
import os, os.path

def printModels(currentID, model_dir):
   c = 0
   print '<MODELS>'
   for root, _, files in os.walk(model_dir):
      for f in files:
         if (currentID in f):            
            print '<M ID="' + str(c) + '">' + f + '</M>'  
            c = c+1
   print '</MODELS>'        
   

if __name__ == "__main__": 
   if len(sys.argv) != 3:
      print "This programs generates ROUGE configuration given the models and peers directory"
      print "Requires 2 arguments <model_dir> <peers_dir>"
      print "To match models and peers will be used the first component of the finaname (the part before the first .)"
      sys.exit(0)
      
   model_dir = sys.argv[1]
   peer_dir = sys.argv[2]
  
   last_peer_id = ""
   
   task = 1
   c = 1;
   
   print '<ROUGE_EVAL version="1.55">'
   print ''
   
   
   for root, _, files in os.walk(peer_dir):
      files.sort() 
      for f in files:
         if f[0] == '.':
            continue
         last_peer_id = '.'.join(f.split('.')[:-1]).upper() #First token in the filename is the task ID!
         print '<EVAL ID="TASK_'+str(task)+'">'
         print '<MODEL-ROOT>' + model_dir +  '</MODEL-ROOT>'
         print '<PEER-ROOT>' + peer_dir +  '</PEER-ROOT>'
         print '<INPUT-FORMAT TYPE=\"SPL\"></INPUT-FORMAT>'
         #Print (single) peer
         print '<PEERS>'         
         print '<P ID="0">' + f + '</P>'         
         print '</PEERS>'
         #Print models for this task
         printModels(last_peer_id, model_dir)
         print '</EVAL>'
         print ''
                 
         task +=  1
         c = c+1
   
   #Close file
   print ''            
   print '</ROUGE_EVAL>'           
