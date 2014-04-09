1 - Extract documents from the DUC directory to my project doc directory

python extractDocs.py ./duc2004/docs/ ./docs/

============

2 - Extract models from the DUC directory to my project directory
This also renames the files

python extractModels.py ./duc2004/eval/models/1/ ./models/

============


3 - Generate ROUGE configuration file.

python generateRougeScript.py ./models/ ./peers/ > settings.xml

NB: does not supports multiple peers so for every docset ID it expects only 1 peer file with the corresponding headline
NB: the docset ID is the first component in the filename of both models and peers (the token before the first .).

============

4 - Run ROUGE

sudo perl ROUGE-1.5.5.pl -e ./ROUGE/RELEASE-1.5.5/data/ -a -c 95 -b 75 -m -n 2 -x -w 1.2 settings.xml > rougeResults.txt

