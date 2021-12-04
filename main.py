import pymongo
import json

import numpy as np

from sklearn.metrics.pairwise import cosine_similarity

from flask import Flask

app = Flask(__name__)

client = pymongo.MongoClient('mongodb://13.124.215.192:27017/')

users = list(client['ssgp']['user'].find())
items = list(client['ssgp']['product'].find())

user_map = {
    usr['_id']: i
    for i, usr in enumerate(users)
}

def similarity_array():
    item_cnt = len(items)
    user_cnt = len(users)

    array = np.zeros((user_cnt, item_cnt), dtype=float)
    for i, item in enumerate(items):
        for u in item['likeUserIds']:
            array[user_map[u], i] = 1

    return array

def predict(user_id, item_id):
    nearby_user = sorted(
        [(i, item) for i, item in enumerate(user_sim_arr[user_map[user_id]])],
        key=lambda x: x[1],
        reverse=True
    )[1:]
    if len(nearby_user) > 5: nearby_user = nearby_user[:5]

    item_users = items[item_id]['likeUserIds']

    # _prd: 가장 유사한 유저 5명의 정보를 이용해 예측한 item_id에 대한 선호도
    if sum(sim for _, sim in nearby_user) != 0:
        _prd = sum((x in item_users) * sim for x, sim in nearby_user) / sum(sim for _, sim in nearby_user)
    else:
        _prd = 0
    
    if np.isnan(_prd):
        _prd = 0

    return _prd

array = similarity_array()

item_sim_arr = cosine_similarity(array.T)
user_sim_arr = cosine_similarity(array)

def extract_sellings(sellingss):
    dct = [{
        'brand': sellings['brand'],
        'content': sellings['content'],
        'selling_price': sellings['sellingPrice'],
        'price': sellings['price']
    } for sellings in sellingss]
    return dct
    
def extract_image_path(sellings):
    return sellings[0]['imagePath']

@app.route('/recommand/<user_id>')
def recommand(user_id):
    recom = sorted(
        [
            (
                {
                    'product_id': str(items[i]['_id']),
                    'name': items[i]['name'],
                    'sellings': extract_sellings(items[i]['sellings']),
                    'image_path': extract_image_path(items[i]['sellings']),
                    'price': min([x['price'] for x in items[i]['sellings']]),
                    'like_count': len(items[i]['likeUserIds'])
                }, 
                predict(user_id, i)
            )
            for i, _ in enumerate(items) if 0 not in _['likeUserIds']
        ],
        key=lambda x: x[1],
        reverse=True
    )

    recom = [x[0] for x in recom]

    return json.dumps(recom)

if __name__ == '__main__':
    app.run(host='0.0.0.0')