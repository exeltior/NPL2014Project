import json
import urllib
import sys
import codecs
from authentication import GOOGLE_API_KEY

def search(query):
    service_url = 'https://www.googleapis.com/freebase/v1/search'
    params = {
            'query': query,
            'key': GOOGLE_API_KEY
    }
    url = service_url + '?' + urllib.urlencode(params)
    response = json.loads(urllib.urlopen(url).read())
    
    best_score = 0
    best_id = None
    
    for result in response['result']:
        if result['score'] > 200 and 'id' in result and 'name' in result:
            score = result['score'] * checkConsistency(query, result['name'])
            if score > best_score:
                best_score = score
                best_id = result['id']    
    return best_id, best_score
        
  
def getAliasFromID(idd):
    service_url = 'https://www.googleapis.com/freebase/v1/topic' + idd
    query = [{'key':GOOGLE_API_KEY,'id': id, 'name': None, '/common/topic/alias':[]}]
    params = {
    }
    url = service_url + '?' + urllib.urlencode(params)
    response = json.loads(urllib.urlopen(url).read())
    properties = response['property']
    
    name =  properties['/type/object/name']['values'][0]['text']
    aliases = []   
    
    if '/common/topic/alias' in properties:
        for e in properties['/common/topic/alias']['values']:
            if isAscii(e['text']):
                aliases.append(e['text'])
    
    isPerson = False
    if '/type/object/type' in properties:
        for e in properties['/type/object/type']['values']: 
            if (e['text'] == 'Person'):
                isPerson = True
                break
    
    return name, aliases, isPerson
    

def compressEntityName(original):
    original = original.replace("\n", "")

    print "Requested compression for entity: " + original
    original_len = len(original)
    
    best_id = None
    best_id_score = 0
    best_subquery = None
    candidates = {}
    partials = {}
    
    # Try subqueries
    for query in getSubsequences(original):
        print 'Trying subquery: ' + query
        candidate = None
        candidate_len = original_len
    
        idd, score = search(query)
        if (idd):
            name, alias, isPerson = getAliasFromID(idd) # already return best match
            if isPerson:
                score *= 5
            print 'Candidate entity (' + str(score) + '): ' + idd + (' - person' if isPerson else '')
            candidates[idd] = candidates.get(idd, 0) + score
            #partials[idd] = partials.get(idd, []).append((score, query))
    
    # Pick best one
    for k, v in candidates.iteritems():
        if (v > 100 and v > best_id_score):
            best_id_score = v
            best_id = k
                
    # Check if one exist
    if not best_id:
        print "No Freebase ID found for '" + original + "'"      
        return original
    
    print '--> Most likely entity found: ' + best_id
    
    name, alias, isPerson = getAliasFromID(best_id) # already return best match

    if not checkConsistency(original, name):
        print "No consistent entity ('"+name+"') for '"+original+"'"      
        return original
    
    if isPerson and len(name.split()) == 2:
        printlog(original, name.split()[-1])
        return name.split()[-1]
    
    alias.append(name)
    
    if isPerson:
        printlog(original, name)
        return name
    else:
        for i in alias:
            if len(i) < candidate_len:
                candidate = i
                candidate_len = len(i)
        if candidate:
            printlog (original, candidate)
            return candidate
        else:
            printlog (original, original)
            return original

def getSubsequences(original):
    s = original.split(' ')
    result = []
    if len(s) <= 2:
        return [' '.join(s)]
    
    for l in range(2, 1+len(s)):
        for start in range(1+len(s)-l):
            result.append(' '.join(s[start:start+l]))
    return result
            
    
def checkConsistency(original, new):
    o = set(original.lower().split())
    n = set(new.lower().split())
    intersection = o.intersection(n)
    union = o.union(n)
    
    if len(intersection) > 0.3*len(o):
        if len(union-intersection) == 0:
            return 100 # very high value... this is very likely the best
        else:
            return len(o.intersection(n))
    else:
        return 0
    
def isAscii(s):
    try:
        s.decode('ascii')
    except:
        return False
    else:
        return True   
    
def printlog(original, new):
    if original == new:
        print bcolors.FAIL + "No compression for entity: " + original + bcolors.ENDC
    else:    
        print bcolors.OKGREEN + "Entity compression: " + original + " --> " + new + bcolors.ENDC

        
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


if __name__ == "__main__":
    string = ''
    for line in sys.stdin:
        string = string + line 
    print compressEntityName(string)



#def googleBestResult(searchfor):
    #for url in gsearch(searchfor, stop=1):
        #print 'Best Google result: ' +  url
        #return url

#def googleBestResult(searchfor):
    #query = urllib.urlencode({'q': searchfor})
    #url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' % query
    #search_response = urllib.urlopen(url)
    #search_results = search_response.read()
    #results = json.loads(search_results)
    #data = results['responseData']
    #hits = data['results']
    #for i in hits:
        #print i['url'] + ' -- ' + i['title']
    #if len(hits):
        #return hits[0]['url']

#def getAliasFromId(id):   
    #service_url = 'https://www.googleapis.com/freebase/v1/mqlread'
    #query = [{'id': id, 'name': None, '/common/topic/alias':[]}]
    #params = {
            #'query': json.dumps(query),
    #}
    #print params
    #url = service_url + '?' + urllib.urlencode(params)
    #response = json.loads(urllib.urlopen(url).read())
    #result = response['result'][0]
    #print result
    #return result['name'], result['/common/topic/alias']