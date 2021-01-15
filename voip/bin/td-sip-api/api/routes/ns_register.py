# -*- coding: utf-8 -*-
from flask_restplus import Resource, fields
from api import (sip_server, redis_client, ns_register as api)

register = api.model('register', {
    'result': fields.Boolean,
    'code': fields.Integer,
})

@api.route('/<username>')
@api.doc(params={'username': 'Имя домофона или sip-аккаунта'})
class Register(Resource):
    def get(self, username):
        """ Получаение данных о регистрации {username} """
        result = False
        message = {}
        username = username.replace(":", "").lower().split("@")[0]
        # location:usrdom::186882308852:televoip.is74.ru
        usrdom = "location:usrdom::{}:{}".format(username, sip_server)
        res = redis_client.smembers(usrdom)
        for item in res:
            # location:entry::uloc-5e303dd6-4656-5da96
            status = redis_client.hgetall(item)
            if status:
                result = True
                message.update(status)
        if result:
            return {'result': result, 'code': 200, 'message': [message]}, 200
        else:
            return {'result': result, 'code': 404, 'message': [message]}, 200
