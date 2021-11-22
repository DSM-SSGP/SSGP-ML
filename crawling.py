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

    return list(item_list.values())

# 할인하지 않는 상품들에 대한 정보들도 저장은 해 놓아야 할 것이다.
# 추천 알고리즘 등에 활용하기 위해 필요한 것들이다.

# 이전에 갖고 있던 상품 목록들도 클러스터링에 추가해서 함께 클러스터링한 후, 
# 이전에 상품 목록에 포함되어 있던 상품들이 어떤 클러스터 안에 존재하는 경우 그 클러스터의 이름은 이전에 갖고 있던 이름으로 고정한다.
# 이전에 상품 목록에 포함되어 있던 상품들이 어떤 클러스터 안에 존재하지 않는 경우 {"name": 상품명, "conv": []}의 형태로 저장해놓고, 쿼리할 때 거른다.

# ↑ 나중에 이거 함
if __name__ == '__main__':
    client = pymongo.MongoClient('mongodb://13.124.215.192:27017/')
    db = client['ssgp']['product']

    pre = pd.DataFrame(db.find({}, {"_id": False, "name": True}))
    
    df = getPageAll()
    item_list = clustering(df, pre)

    db.update_many({}, {"$set": {"sellings": []}})
    for item in tqdm(item_list):
        db.update_one({'name': item['name']}, {'$set': {'sellings': item['sellings']}}, upsert=True)
    
    db.update_many({'likeUserIds': {"$exists": False}}, {'$set': {'likeUserIds': []}})
    
    print(len(item_list))