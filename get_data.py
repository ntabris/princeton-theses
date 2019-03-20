import re
import operator
import json
import urllib.request
import pandas as pd
import numpy as np

def get_data(filename,url):
    j = ''
    try:
        f = open('data/%s.json'%filename,'r')
        j = f.read()
        f.close()
        print("Using saved data for %s." % filename)
    except:
        req = urllib.request.Request(url,headers={'Accept': 'application/json'})
        res = urllib.request.urlopen(req)
        
        j = res.read().decode('utf-8')

        f = open('data/%s.json'%filename,'w')
        f.write(j)
        f.close()
        print("Downloaded %s data and saved for future use." % filename)
    return j

def item_process(json_string,id=''):
    json_struct = json.loads(json_string)
    data = dict()
    key_list = ("dc.contributor.advisor","dc.contributor.author","dc.date.created","dc.format.extent","dc.title","pu.date.classyear")
    if id:
        data['id'] = id
    for key in key_list:
        key_trunc = key.split('.')[-1]
        data[key_trunc] = None
    for item in json_struct:
        key = item['key']
        key_trunc = key.split('.')[-1]
        
        val = item['value']
        if key_trunc == 'extent':
            # remove non-numeric (" pages") from extent
            val = re.sub(r'[^\d]','',val)
        
        if key in key_list:
            data[key_trunc] = val
    
    return data

def get_list():
    url = 'https://dataspace.princeton.edu/rest/collections/395/items?limit=3000'
    filename = 'list'
    return get_data(filename,url)

if __name__ == '__main__':
    j = get_list()
    print("data size:",len(j))

    list_json = json.loads(j)
    ids = [ i['id'] for i in list_json ]
    
    print('item count:',len(ids))
    
    data = dict()
    
    for id in ids:
        u = 'https://dataspace.princeton.edu/rest/items/%s/metadata' % id
        n = 'item_%s'%id
        json_string = get_data(n,u)
        data[id] = item_process(json_string,id)
        data[id]['id'] = id
    
    
    df = pd.DataFrame( data ).transpose()
    
    df['classyear'] = pd.to_numeric( df['classyear'] )
    df['extent'] = pd.to_numeric( df['extent'] )
    
    df.to_csv('data/senior_theses.csv')