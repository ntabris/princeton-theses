import re
import operator
import json
import urllib.request
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
    
def fix_advisors(df):
    advisor_hist = df.groupby('advisor').count().loc[:,('id')].to_dict()
    for name in advisor_hist.keys():
        norm_name = normalize_name(name,advisor_hist)
        if name != norm_name:
            #print(name,"=>",norm_name)
            df.loc[df.advisor == name,'advisor'] = norm_name


def normalize_name(this_name,names):
    if not this_name:
        return this_name
    
    unchanged = this_name
    
    if this_name.count(',') == 0:
        this_name = re.sub(r'^(.*) (\w+)$',r'\2, \1',this_name)
        
    name_core = this_name
    # replace this name with longest matching name
    # ideally we would make sure we don't do this when ambiguous (last => dif firsts)
    name_core = re.sub(r'^(.+),\s+(\w).*$',r'\1, \2',name_core)
    
    # if van, remove
    name_core = re.sub(r'^(van ?)',r'',name_core)
    
    # specific fixes to incorrect data
    name_core = re.sub('Fraasen','Fraassen',name_core)
    name_core = re.sub('Nehemas','Nehamas',name_core)
    name_core = re.sub('Graff, D','Fara, D',name_core)
    
    matches = [ name for name in names.keys() if name is not None and name.find(name_core) > -1]
    
#   print(name_core,"/",this_name,":","; ".join(matches))
    
    if len(matches):
        matches.sort(key=lambda x: (len(x),x),reverse=True)
        this_name = matches[0]
    
#     if this_name != unchanged:
#         print(unchanged,"=>",this_name)
    
    return this_name

def show_advisor_by_decade(df):
    for year in range(1940,2020,10):
        decade = df.query('classyear >= %d and classyear < %d' % (year,year+10))
        len_mean = decade['extent'].mean()
        len_std = decade['extent'].std()
        advisor_mode = '; '.join(decade['advisor'].mode())
        print(year,"-",year+9,":",round(len_mean),"pages (",round(len_std,3),"std )",advisor_mode ) 

def show_advisor_by_year(df):
    for year in range(2000,2018):
        print("YEAR:\t%d"%year)
        advisor_counts = df[df.classyear==year].groupby('advisor').count()
        print(advisor_counts.loc[:,'id'].sort_values(ascending=False))
    
def other(data):
    
    advisors = set( data[d]['dc.contributor.advisor'] for d in data )

#     for name in advisors:
#         norm_name = normalize_name(name,advisors)
#         if name != norm_name:
#             print(name,"=>",norm_name)

    advisor_counts = dict()

    for d in data.values():
        advisor = normalize_name(d['dc.contributor.advisor'],advisors)
        year = d['pu.date.classyear']
        advisor_counts[advisor] = advisor_counts.get(advisor,0) + 1
    
    advisors_sorted = sorted(advisor_counts.items(), key=operator.itemgetter(1),reverse=True)
    
    for i,(advisor,count) in enumerate(advisors_sorted):
        if advisor is not None:
            print("%s\t%s" % (count,advisor) )
            
def plot_pages_by_year(df):
    scatter_by_year = []
    year_labels = []
    for year in range(1988,2017):
        if year % 2 == 0:
            year_labels.append(year)
        else:
            year_labels.append('')
        scatter_by_year.append( df[df.classyear == year]['extent'] )
        
    
    #print(scatter_by_year)
    
    plt.boxplot(scatter_by_year,labels=year_labels)
    plt.title("Length of Princeton Senior Thesis")
    plt.xlabel("Class Year")
    plt.ylabel("Pages")
    plt.show()
    
def sea_pages_by_year(df):
    g = sns.boxplot(x="classyear", y="extent",
        data=df[df.classyear >= 1988],
        palette="Blues_r"
    )
    labels = g.get_xticklabels()
    for i in range(1,len(labels),2):
        labels[i]=None
    g.set_xticklabels(labels)
    g.set(xlabel="Graduating Year",ylabel="Average Thesis Length")
    
    plt.show()
    
def count_by_year(df):
    #bins = range(df['classyear'].min(),df['classyear'].max()+1)
    year_hist = plt.hist(df['classyear'],bins=df['classyear'].sort_values())
    print(year_hist)
    plt.show()
    
def plot_advisor_counts(df):
    advisor_hist = plt.hist(
        df.groupby('advisor').count().loc[:,'id'],
        bins=df['advisor'].nunique()
    )
    plt.show()

def stackplot_advisor_by_year(df):
    # NOT GOOD VISUALLY
    # stackplot of (advisor, number of advisees per year)
    
    advisor_idx = {}    # hash to map advisor name to index in advisor_data
    advisor_data = []   # where we'll yearly data for each advisor
    
    # dict of advisors,counts for whole period
    # this tells us who to track
    advisors = df[df.classyear>=1998] \
        .groupby('advisor') \
        .count() \
        .loc[:,'id'] \
        .sort_values() \
        .to_dict()
    for advisor,count in advisors.items():
        if count > 15:
            advisor_idx[advisor] = len(advisor_data)
            advisor_data.append([])
        else:
            advisor_idx[advisor] = -1 # for advisors grouped as "other"
    
    # add extra array for "other" data
    advisor_data.append([])
    
    # collect year by year counts
    for year in range(1998,2018):
        year_counts = df[df.classyear==year].groupby('advisor').count() \
            .loc[:,'id'].to_dict()
        # insert 0 for every advisor for this year
        for i in range(len(advisor_data)):
            advisor_data[i].append(0)
        # now insert real count for each advisor, if not 0
        year_idx = len(advisor_data[i]) - 1
        for advisor in year_counts:
            idx = advisor_idx[advisor]
            idx = len(advisor_data)-1 if idx == -1 else idx
            advisor_data[idx][year_idx] = year_counts[advisor]
    
    for advisor,idx in advisor_idx.items():
        if idx > -1:
            print(advisor,":",advisor_data[idx])
            
    print("OTHER:",advisor_data[ len(advisor_data)-1 ])
    
    plt.stackplot(range(1998,2018),advisor_data)
    plt.show()

if __name__ == '__main__':

    #df = feather.read_dataframe('data/senior_theses.feather')
    df = pd.read_csv('data/senior_theses.csv')
    
    #print(df.head())
    
    fix_advisors(df)
    
    # how many advisors have exactly one advisee
    print(df.groupby('advisor').count().query('id == 1').shape)
    
    # histogram of advisor/advisee counts
    h = df.groupby('advisor').count().groupby('id').count().loc[:,('author')]
    print(h)
    print(h.shape)
    
#    stackplot_advisor_by_year(df)
    
#     df[df.classyear>=1998].groupby('advisor').count().loc[:,'id']
    
    
    #print( df.loc[:,('advisor','id')].groupby('advisor').count().sort_values('id') )
    
    # scatterplot of thesis length by year
    plt.scatter('classyear','extent',data=df[df.classyear >= 1988],alpha=0.5)
    plt.show()