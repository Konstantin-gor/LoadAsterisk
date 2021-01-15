# -*- coding: utf-8 -*-
import requests
from api import (redis_client, ns_channel as api)
from flask_restplus import Resource, abort, fields

call = api.model('call', {
    'result': fields.String,
    'code': fields.Integer,
    'call': fields.String,
})


@api.route('/<username>')
@api.doc(params={'username': 'Имя пользователя. Допустимо использовать mac адрес через `:`'})
class Channel(Resource):
    @api.response(404, description='На устройстве нет вызова')
    @api.response(400, description='Не узказан username')
    def get(self, username):
        """Информация о наличии звонка с указанного ТД с {username}"""
        if username == "":
            abort(400)
        username = username.replace(":", "").lower().split("@")[0]
        call = redis_client.get("call::{}".format(username))
        if call:
            return {'result': 'Channel found on televoip', 'code': 200, 'call': call}, 200
        else:
            abort(404, message="На устройстве нет вызова")
