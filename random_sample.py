# -*- coding: utf-8 -*-
__author__ = 'sincat'

# 加载django环境
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import redis
import random
import json

STORE_OPTIONS = {
    'host': 'localhost',
    'port': 6379,
    'password': '',
    'db': 3
}

global_rd = redis.StrictRedis(**STORE_OPTIONS)

from flask import Flask, request, jsonify
app = Flask(__name__)


@app.route("/")
def welcome():
    print 'welcome'
    return "use random sample!"

@app.route("/init", methods=['POST'])
def init():
    if request.method == 'POST':
        id_list = request.json['ids']
        global_rd.hset('id_pool', 'ids', id_list)
        global_rd.bgsave()
        return jsonify({
            'ret': 0,
            'msg': 'OK'
        })

@app.route("/sample/<open_id>/<num>", methods=['GET'])
def get_random_sample(open_id, num):
    if request.method == 'GET':
        id_dict = global_rd.hgetall(open_id)
        num = int(num)
        if id_dict:
            print id_dict['id_list']
            sid_list = json.loads(id_dict['id_list'])
            index = int(id_dict['index'])

            global_rd.hset(open_id, 'index', index + num)
            global_rd.expire(open_id, 600)
            random_ids = sid_list[index:num+index]
            return jsonify({
                'ret': 0,
                'random_ids': random_ids
            })
        else:
            id_list = global_rd.hget('id_pool', 'ids')
            id_list = json.loads(id_list)
            sid_list = random.sample(id_list, len(id_list))
            global_rd.hset(open_id, 'index', num)
            global_rd.hset(open_id, 'id_list', sid_list)
            global_rd.expire(open_id, 600)
            random_ids = sid_list[:num]
            return jsonify({
                'ret': 0,
                'random_ids': random_ids
            })

if __name__ == "__main__":
    app.run(debug=True)
