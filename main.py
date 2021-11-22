import pymongo
import json

import numpy as np
import random

from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity

from flask import Flask

app = Flask(__name__)

client = pymongo.MongoClient('mongodb://13.124.215.192:27017/')

users = list(client['ssgp']['user'].find())
items = list(client['ssgp']['product'].find())

def similarity_array(transpose):
    item_cnt = len(items)
    user_cnt = len(users)

    array = np.zeros((user_cnt, item_cnt), dtype=float)
    for i, item in enumerate(items):
        for u in item['likeUserIds']:
            array[u, i] = 1

    if transpose: array = array.T

    sim = cosine_similarity(array)
    return sim

def predict(user_id, item_id):
    user_idx = -1
    for user in users:
        if user['id'] == user_id:
            user_idx += 1
            break

        user_idx += 1

    if user_idx == -1:
        return

    nearby_user = sorted(
        [(i, item) for i, item in enumerate(user_sim_arr[user_id])],
        key=lambda x: x[1],
        reverse=True
    )[1:]
    if len(nearby_user) > 5: nearby_user = nearby_user[:5]

    item_users = items[item_id]['likeUserIds']

    # _prd: 가장 유사한 유저 5명의 정보를 이용해 예측한 item_id에 대한 선호도
    _prd = sum((x in item_users) * sim for x, sim in nearby_user) / sum(sim for _, sim in nearby_user)
    if _prd == np.nan: 
        _prd = 0

    return _prd

item_sim_arr = similarity_array(transpose=True)
user_sim_arr = similarity_array(transpose=False)

@app.route('/recommand/<user_id>')
def recommand(user_id):
    recom = sorted(
        [(i, predict(user_id, i)) for i, _ in tqdm(enumerate(items)) if 0 not in _['likeUserIds']],
        key=lambda x: x[1],
        reverse=True
    )

    if not any([x[1] for x in recom]):
        recom = sorted(recom, key=lambda _: random.random())

    return json.dumps(recom[:5])

if __name__ == '__main__':
    app.run()