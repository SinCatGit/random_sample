# -*- coding: utf-8 -*-
__author__ = 'sincat'

# 加载django环境
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import redis
import random
import json
from conf import STORE_OPTIONS

global_rd = redis.StrictRedis(**STORE_OPTIONS)

from flask import Flask, request, jsonify
app = Flask(__name__)


@app.route("/")
def welcome():
    return "use random sample!"

@app.route("/init", methods=['POST'])
def init():
    if request.method == 'POST':
        id_list = request.json['ids']
        app_name = request.json['app_name']
        global_rd.mset({
            app_name+':id_pool': id_list
        })
        global_rd.bgsave()
        return jsonify({
            'ret': 0,
            'msg': 'OK'
        })

@app.route("/sample/<app_name>/<open_id>/<num>", methods=['GET'])
def get_random_sample(app_name, open_id, num):
    if request.method == 'GET':
        open_id_list = global_rd.get(app_name+':'+open_id+':id_list')
        num = int(num)
        if open_id_list is None:
            id_list = global_rd.get(app_name+':id_pool')
            id_list = json.loads(id_list)
            sid_list = random.sample(id_list, len(id_list))
            global_rd.mset({app_name + ':' + open_id+':index': num})
            global_rd.mset({app_name + ':' + open_id+':id_list': sid_list})
            global_rd.expire(app_name + ':' + open_id+':index', 600)
            global_rd.expire(app_name + ':' + open_id+':id_list', 600)
            random_ids = sid_list[:num]
            return jsonify({
                'ret': 0,
                'random_ids': random_ids
            })
        else:
            sid_list = json.loads(open_id_list)
            index = int(global_rd.get(app_name+':'+open_id+':index'))
            sid_list_len = len(sid_list)
            if index+num >= sid_list_len:
                random_ids = sid_list[index:]
                random_ids.extend(sid_list[0:index+num-sid_list_len])
                global_rd.mset({app_name+':'+open_id+':index':index+num-sid_list_len})
                global_rd.expire(app_name + ':' + open_id+':index', 600)
                global_rd.expire(app_name + ':' + open_id+':id_list', 600)
                return jsonify({
                    'ret': 0,
                    'random_ids': random_ids
                })
            else:
                global_rd.mset({app_name+':'+open_id+':index':index + num})
                global_rd.expire(app_name + ':' + open_id+':index', 600)
                global_rd.expire(app_name + ':' + open_id+':id_list', 600)
                random_ids = sid_list[index:num+index]
                return jsonify({
                    'ret': 0,
                    'random_ids': random_ids
                })


@app.route("/append", methods=['POST'])
def append():
    if request.method == 'POST':
        id_list = request.json['ids']
        app_name = request.json['app_name']

        id_pool_list = json.loads(global_rd.get(app_name+':id_pool'))
        id_pool_list.extend(id_list)
        global_rd.mset({
            app_name+':id_pool': id_pool_list
        })
        global_rd.bgsave()
        return jsonify({
            'ret': 0,
            'msg': 'OK'
        })

@app.route("/delete", methods=['POST'])
def delete():
    if request.method == 'POST':
        id_list = request.json['ids']
        app_name = request.json['app_name']

        id_pool_list = json.loads(global_rd.get(app_name+':id_pool'))
        id_pool_set = set(id_pool_list)
        id_pool_list = list(id_pool_set - set(id_list))
        global_rd.mset({
            app_name+':id_pool': id_pool_list
        })
        global_rd.bgsave()
        keys = global_rd.keys('*:id_list')
        for key in keys:
            id_pool_list = json.loads(global_rd.get(key))
            id_pool_set = set(id_pool_list)
            id_pool_list = list(id_pool_set - set(id_list))
            index = int(global_rd.get(key[:-7]+'index'))
            if index >= len(id_pool_list):
                global_rd.mset({
                    key[:-7]+'index': 0
                })
            global_rd.mset({
                key: random.sample(id_pool_list, len(id_pool_list))
            })
        return jsonify({
            'ret': 0,
            'msg': 'OK'
        })

import optparse

def flaskrun(app, default_host="127.0.0.1",
                  default_port="5000"):
    """
    Takes a flask.Flask instance and runs it. Parses
    command-line flags to configure the app.
    """

    # Set up the command-line options
    parser = optparse.OptionParser()
    parser.add_option("-H", "--host",
                      help="Hostname of the Flask app " + \
                           "[default %s]" % default_host,
                      default=default_host)
    parser.add_option("-P", "--port",
                      help="Port for the Flask app " + \
                           "[default %s]" % default_port,
                      default=default_port)

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug",
                      help=optparse.SUPPRESS_HELP)
    parser.add_option("-p", "--profile",
                      action="store_true", dest="profile",
                      help=optparse.SUPPRESS_HELP)

    options, _ = parser.parse_args()

    # If the user selects the profiling option, then we need
    # to do a little extra setup
    if options.profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                       restrictions=[30])
        options.debug = True

    app.run(
        debug=options.debug,
        host=options.host,
        port=int(options.port)
    )

if __name__ == "__main__":
    app = Flask(__name__)
    flaskrun(app)
