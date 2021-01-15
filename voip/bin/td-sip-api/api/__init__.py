#!/usr/bin/python
# -*- coding: utf8 -*-
__author__ = 'Abdulin Valentin'
__version__ = '2.0.0'

import json
from sys import path
from flask import Flask
from flask_restplus import Api, reqparse
from flaskext.mysql import MySQL
from flask_redis import FlaskRedis
from pymysql.cursors import DictCursor

path.insert(0, '/usr/local/voip/lib/python')
from TdCallsManager import Log

script_name = 'td-sip-api'
cfg_name = '/usr/local/voip/etc/td-sip-api.json'
#cfg_name = './etc/td_ari_config.json'
with open(cfg_name) as c:
    cfg = json.load(c)
if not cfg:
    print("Не найден файл конфигурации")

# Variables
sip_server = cfg.get("sip_server")

# This api config
api_cfg = cfg.get("td-sip-api")
api_host = api_cfg.get("host", "0.0.0.0")
api_port = api_cfg.get("port", "9080")

# log
log_cfg = cfg.get("logger")
log_dir = log_cfg.get("dir", "./")
log_level = log_cfg.get("level", "info")
log_filename = "{}/{}.log".format(log_dir, script_name)
log = Log()
log.set_log_file(log_filename, log_level)

# MYSQL
mysql_cfg = cfg.get("mysql")

# redis-televoip
redis_cfg = cfg.get("televoip_redis")
redis_table_location = 1
redis_url = "redis://{}:{}/{}".format(redis_cfg.get('host'), redis_cfg.get('port'), redis_table_location)

# APPLICATION
app = Flask(__name__)
api = Api(app=app,
          version='1.0',
          title='TD-VOIP-API',
          description='Внешнее API для работы с для работы с televoip sip-сервером'
                      '<style>.models {display: none !important}</style>',
          contact_email='valiko@intersvyaz.net',
          doc='/doc')

app.config['RESTPLUS_MASK_SWAGGER'] = False
app.config['MYSQL_DATABASE_HOST'] = mysql_cfg.get("host", "localhost")
app.config['MYSQL_DATABASE_PORT'] = mysql_cfg.get("port", 3306)
app.config['MYSQL_DATABASE_USER'] = mysql_cfg.get("user")
app.config['MYSQL_DATABASE_PASSWORD'] = mysql_cfg.get("password")
app.config['MYSQL_DATABASE_DB'] = mysql_cfg.get("database")
app.config['REDIS_URL'] = redis_url

mysql = MySQL(cursorclass=DictCursor, autocommit=True)
redis_client = FlaskRedis(decode_responses=True)

mysql.init_app(app)
redis_client.init_app(app)

authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
    }
}

####################################################
############# регистрируем нэймспейсы ##############
####################################################
ns_channel = api.namespace(
    'channel',
    description='<marquee>Работа со звонками/каналами в рамках комплекса televoip.</marquee>',
    path='/channel',
    validate=True,
    ordered=True
)
ns_account = api.namespace(
    'account',
    description='<marquee> Работа с аккаунтами на SIP сервере. Заведение, удаление и т.п. </marquee>',
    path='/account',
    authorizations=authorizations,
    validate=True,
    ordered=True
)

ns_register = api.namespace(
    'register',
    description='<marquee> Данные  по регистрациям </marquee>',
    path='/register',
    authorizations=authorizations,
    validate=True,
    ordered=True
)

####################################################

from api.routes import *
