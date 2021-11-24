from pyonyScrapper import getPageAll
from stringDistance import subst_dist

from sklearn.cluster import DBSCAN
from tqdm import tqdm

import numpy as np
import pandas as pd

import pymongo

def clustering(df, before, metric=subst_dist):
    if len(before.columns) == 0:
        before['name'] = pd.Series([], dtype=object)
    
    before_set = set(before['name'])

    def get_map(data):
        distance_matrix = np.zeros((len(data), len(data)), dtype=float)

        for j in tqdm(range(len(data)), desc='clustering names.......'):
            for i in range(j, len(data)):
                distance_matrix[j, i] = metric(data[j], data[i])
                distance_matrix[i, j] = distance_matrix[j, i]
                
        datas = np.asarray(data)
        dbscan = DBSCAN(eps=0.2, min_samples=1, metric='precomputed')
        dbscan.fit(distance_matrix)

        maps = {}
        for cluster_id in np.unique(dbscan.labels_):
            cluster = datas[np.nonzero(dbscan.labels_==cluster_id)]
            
            cluster_name = None
            for cluster_item in cluster:
                if cluster_item in before_set:
                    cluster_name = cluster_item
                    break
            
            if cluster_name is None:
                cluster_name = cluster[0]

            for cluster_item in cluster:
                maps[cluster_item] = cluster_name
        
        return maps
    
    strs = np.unique(
        np.concatenate(
            (np.asarray(df['name']), np.asarray(before['name']))
        )
    )
    maps = get_map(strs)

    item_list = {
        x: {
            'name': x,
            'sellings': []
        } 
        for x in set(maps.values()) 
    }

    for item in df.iloc:
        key = maps[item['name']]

        # { "brand" : "CU", "price" : 14900, "sellingPrice" : 7450, "content" : "1+1" }

        finded = False
        for conv in item_list[key]['sellings']:
            if conv['brand'] == item['conv']:
                finded = True
                break
        
        if finded:
            continue

        item_list[key]['sellings'].append({
            'brand':        item['conv'],
            'price':        int(item['cost']),
            'sellingPrice': int(item['price']),
            'content':      item['event'],
            'imagePath':    item['path']
        })

    for item in before.iloc:
        key = maps[item['name']]

        if item_list.get(key) != None:
            continue

        item_list[key] = {"name": item["name"], "sellings": []}

    return list(item_list.values())

if __name__ == '__main__':
    client = pymongo.MongoClient('mongodb://13.124.215.192:27017/')
    db = client['ssgp']['product']

    pre = pd.DataFrame(db.find({}, {"_id": False, "name": True}))
    
    df = getPageAll()
    item_list = clustering(df, pre)

    db.delete_many({})
    db.insert_many(item_list)
    
    db.update_many({'likeUserIds': {"$exists": False}}, {'$set': {'likeUserIds': []}})
    
    print(len(item_list))