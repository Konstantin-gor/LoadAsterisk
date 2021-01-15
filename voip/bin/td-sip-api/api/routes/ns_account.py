# -*- coding: utf-8 -*-
from flask_restplus import Resource, fields, abort, reqparse
from api import ns_account as api

from api.routes.account import Account

jff_desc = '<img src=https://img.artlebedev.ru/everything/stickers/ohuenny/als-stiker-ohuenny-016+.gif width=100 height=100></img>'
simple_account = api.model('account', {
    'username': fields.String,
    'domain': fields.String,
})
account_model = api.model('account_pwd', {
    'username': fields.String,
    'domain': fields.String,
    'password': fields.String,
    'ha1': fields.String,
    'ha1b': fields.String

})


@api.route('')
@api.doc()
class Subscriber(Resource):
    @api.param('username', description='Имя пользователя', type=str)
    @api.param('domain', description='SIP-домен', type=str, default='televoip.is74.ru')
    @api.marshal_with(simple_account)
    @api.response(500, description=jff_desc * 12)
    @api.response(404, description='Нет такого пользователя в указанном домене')
    @api.response(400, description='Не узказаны обязательные параметры')
    def get(self):
        """получить информацию об аккаунте"""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, help='Имя пользователя', required=True)
        parser.add_argument('domain', type=str, help='SIP-домен', required=True)
        args = parser.parse_args()
        subscriber = Account(**args)
        result = subscriber.get_user()
        if result:
            return result
        else:
            code = result[1]
            abort(code)


    @api.param('username', description='Имя пользователя', type=str, _in='formData')
    @api.param('domain', description='SIP-домен', type=str, default='televoip.is74.ru', _in='formData')
    @api.param('password', description='Пароль пользователя', type=str, _in='formData')
    @api.marshal_with(simple_account)
    @api.response(400, description='Не переданы обязательные параметры')
    @api.response(409, description='Аккаунт уже существует')
    def post(self):
        """создать новый аккаунт"""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, location='form')
        parser.add_argument('domain', type=str, required=True, location='form')
        parser.add_argument('password', type=str, required=True, location='form')
        args = parser.parse_args()
        subscriber = Account(**args)
        result = subscriber.add_user()
        if result:
            return result
        else:
            code = result[1]
            abort(code)

    @api.param('username', description='Имя пользователя', type=str, _in='formData')
    @api.param('domain', description='SIP-домен', type=str, default='televoip.is74.ru', _in='formData')
    @api.param('password', description='Пароль пользователя', type=str, _in='formData')
    @api.marshal_with(simple_account)
    @api.response(400, description='Не переданы обязательные параметры')
    @api.response(404, description='Аккаунт не существует')
    def put(self):
        """обновить инормацию об аккаунте"""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, location='form')
        parser.add_argument('domain', type=str, required=True, location='form')
        parser.add_argument('password', type=str, required=True, location='form')
        args = parser.parse_args()
        subscriber = Account(**args)
        result = subscriber.update_user()
        if result:
            return result
        else:
            code = result[1]
            abort(code)

    @api.param('username', description='Имя пользователя', type=str, _in='formData')
    @api.param('domain', description='SIP-домен', type=str, default='televoip.is74.ru', _in='formData')
    @api.marshal_with(simple_account)
    @api.response(400, description='Не переданы обязательные параметры')
    @api.response(403, description='Не найден пользователь')
    def delete(self):
        """удалить аккаунт"""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, help='Имя пользователя', required=True, location='form')
        parser.add_argument('domain', type=str, help='SIP-домен', required=True, location='form')
        args = parser.parse_args()
        subscriber = Account(**args)
        result = subscriber.delete_user()
        if result:
            return result
        else:
            code = result[1]
            abort(code)
