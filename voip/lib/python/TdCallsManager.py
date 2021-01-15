#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Для работы с теледомофонами на сип серверах.
"""
import logging
from configparser import ConfigParser
import requests
from datetime import datetime


class Conf(ConfigParser):
    _cfg = {}

    def get_settings(self, path, name):
        cfg_file = '{}/{}.ini'.format(path, name)
        self.read(cfg_file)
        for section in self.sections():
            self._cfg[section] = {}
            for option in self.options(section):
                self._cfg[section][option] = self.get(section, option)
        return self._cfg


class Log:
    def __init__(self):
        self.formatter = logging.Formatter('%(asctime)s,%(msecs)05d %(levelname)s: %(message)s', '%Y-%m-%d,%H:%M:%S')
        self.log = logging.getLogger()
        self.log.setLevel('NOTSET')
        self.stdout_h = logging.StreamHandler()
        self.stdout_h.setFormatter(self.formatter)
        self.log.addHandler(self.stdout_h)
        self.file = None
        self.level = None
        self.file_h = None

    def set_log_file(self, log_file, level):
        self.file = log_file
        self.level = level.upper()
        self.log.setLevel(self.level)
        self.file_h = logging.FileHandler(self.file)
        self.file_h.setFormatter(self.formatter)
        self.log.addHandler(self.file_h)
        self.log.removeHandler(self.stdout_h)

    def critical(self, message):
        self.log.critical(message)

    def error(self, message):
        self.log.error(message)

    def warning(self, message):
        self.log.warning(message)

    def info(self, message):
        self.log.info(message)

    def debug(self, message):
        self.log.debug(message)


class PushOld:
    __log = Log()

    def __init__(self, push_url):
        self.__push_server = push_url

    def multipush(self, teledomophone, uuid_hdr, *args):
        # TODO: разобраться и выпилить хардкод.
        method = 'api'
        td_server = '"sip_dns"'
        td_port = 5060
        __src_uri = 'sip:{}@{}:{}'.format(teledomophone, td_server, td_port)

        # отрезаем у аккаунтов порт
        __accounts = [":".join(item.split(':')[:-1]) for item in args]
        __data = {'from': __src_uri, 'to': __accounts}
        request = '{}/{}'.format(self.__push_server, method)
        self.__log.debug('Request URL: {} and params: {}'.format(request, __data))
        try:
            r = requests.get(request, params=__data)

            if r.status_code == 200:
                response = r.json()
                self.__log.debug('For {} received json: {}'.format(request, response))
                return response
            else:
                self.__log.error('Response with code: {},'
                                 'message: {}, \n'
                                 'headers: {}'.format(r.status_code, r.reason, r.headers))
        except Exception as e:
            self.__log.error(e)

class Push:
    __log = Log()

    def __init__(self, push_url):
        self.__push_server = push_url

    def multipush(self, teledomophone, uuid_hdr, flat, *args):
        # TODO: разобраться и выпилить хардкод.
        method = 'intercom/'
        td_server = '"sip_dns"'
        td_port = 7777
        __src_uri = 'sip:{}@{}:{}'.format(teledomophone, td_server, td_port)

        # отрезаем у аккаунтов порт
        __accounts = [":".join(item.split(':')[:-1]) for item in args]
        for account in args:
            account = account.replace('sip:', '')

            __data = {
                    'mac': teledomophone,
                    'event': 0,
                    'sipaddr1': "%s@%s:%s" % (flat, td_server, td_port),
                    'uuid': uuid_hdr,
            }

            request = '{}/{}'.format(self.__push_server, method)
            self.__log.debug('Request URL: {} and params: {}'.format(request, __data))
            try:
                r = requests.get(request, params=__data)

                if r.status_code == 200:
                    response = r.json()
                    self.__log.debug('For {} received json: {}'.format(request, response))
                    return response
                else:
                    self.__log.error('Response with code: {},'
                                     'message: {}, \n'
                                     'headers: {}'.format(r.status_code, r.reason, r.headers))
            except Exception as e:
                self.__log.error(e)

class Crm:
    """ модуль-прослойка для работы voip с td crm API. """

    __headers = {'Authorization': ''}
    __default_error = {404: 'Not Found'}
    __log = Log()
    __auth_type = 'Bearer'
    __token = ''
    __live_end = None
    __live_start = None

    def __init__(self, **kwargs):
        """
        :param kwargs:
            api_url - базовай url апи td-crm
            api_user - имя пользователя для API
            api_password - пароль для API
            api_buyer_id - ID покупателя, если не задан, будет 1
            push_url - базовый url для пуш сервера (firebase)
        """

        self._td_api_buyer_id = kwargs.get('api_buyer_id') or 1
        self._td_api_user = kwargs.get('api_user')
        self._td_api_password = kwargs.get('api_password')
        self._td_auth_payload = {'BUYER_ID': self._td_api_buyer_id,
                                 'LOGIN': self._td_api_user,
                                 'PASS': self._td_api_password}
        self._td_api_url = kwargs.get('api_url')
        self._push_url = kwargs.get('push_url')

        if kwargs.get('api_token') is not None:
            self._td_api_headers = self.__headers['Authorization'] = '{} {}'.format(self.__auth_type,
                                                                                    kwargs.get('api_token'))
        else:
            self._td_api_headers = self.__get_auth_header()

    def __get_auth_header(self, method='auth', auth_type=__auth_type):
        """
        получаем авторизационный токен
        :param method: какой метод использовать для авторизации, в нашем случае `auth`
        :param auth_type: тип авторизации в api, по умолчанию Bearer.
        :return: словарь в виде заголовков авторизации для дальнейших запросов.
        """
        td_auth_url = '{}/{}'.format(self._td_api_url, method)

        try:
            r = requests.post(td_auth_url, data=self._td_auth_payload)
            if r.status_code == 200:
                auth_data = r.json()
                self.__token = auth_data.get('TOKEN')
                self.__live_end = datetime.strptime(auth_data.get('ACCESS_END'), '%Y-%m-%d %H:%M:%S')
                self.__live_start = datetime.strptime(auth_data.get('ACCESS_BEGIN'), '%Y-%m-%d %H:%M:%S')
                self.__headers['Authorization'] = '{} {}'.format(auth_type, self.__token)
                self.__log.info(
                    'From {} was received token: {}, live_start: {}, live_end: {}'.format(td_auth_url, self.__token,
                                                                                          self.__live_start,
                                                                                          self.__live_end))
                return self.__headers
            else:
                self.__log.error('Response with code: {},\n'
                                 'message: {}, \n'
                                 'headers: {}'.format(r.status_code, r.reason, r.headers))
        except Exception as e:
            self.__log.error(e)

    def __check_token(self):
        try:
            time_now = datetime.now()
            self.__log.info('current time {}, token expiration {}'.format(time_now, self.__live_end))
            if time_now > self.__live_end:
                self.__log.info('the token - {} has expired, let\'s recycle'.format(self.__token))
                self._td_api_headers = self.__get_auth_header()
        except Exception as e:
            self.__log.error(e)

    def __td_api_get(self, uuid_hdr, td_request):
        """
        Обёртка для выполнения get запросов в td-crm.
        Тут же можно реализовать кеширование и получение данных из кеша без апи
        :param td_request:
        :return: json с ответом от сервера или None в случае ошибки или отсутвия данных
        """
        self.__check_token()
        self.__log.debug('Request URL: {}'.format(td_request))
        try:
            r = requests.get(td_request, headers=self.__headers)
            if r.status_code == 200:
                response = r.json()
                self.__log.debug('For {} received json: {}'.format(td_request, response))
                return response
            elif r.status_code == 401:
                self.__log.debug('Response code {}, token expired, let`s recycle'.format(r.status_code))
                self._td_api_headers = self.__get_auth_header()
            else:
                self.__log.error('Response with code: {},'
                                 'message: {},'
                                 'headers: {}'.format(r.status_code, r.reason, r.headers))
        except Exception as e:
            self.__log.error(e)

    def resolve_sip_account(self, teledomophone, flat,
                            uuid_hdr='unknown',
                            method='sip-resolve'):
        """
        Получаем информацию об аккаунтах привязанных к квартире не текущем теледомофоне из td-crm
        auth Bearer
        GET http://td-crm.is74.ru/api/sip-resolve/<teledomophone>:<flat>

        :param teledomophone: sip поле From. id вызывающего теледомофона.
        :param flat: номер набранной на теледомофоне квартиры
        :param uuid_hdr: заголовок UUID, для сквоззного логирования вызова
        :param method: метод вызываемый в td-crm api
        :return: json от td-crm или или None
        """

        td_request = '{}/{}/{}:{}'.format(self._td_api_url, method, teledomophone, flat)
        result = self.__td_api_get(uuid_hdr, td_request)
        if result:
            return result

    def resolve_attached(self, teledomophone,
                         uuid_hdr='unknown',
                         method='sip/{}/resolve-attached'):
        """
        Узнаём привязанные к калитке дома и квартиры.
        auth Bearer
        GET http://td-crm.is74.ru/api/sip/<teledomophone>/resolve-attached
        :param teledomophone: sip поле From. id вызывающего теледомофона.
        :param uuid_hdr: заголовок UUID, для сквоззного логирования вызова
        :param method: метод вызываемый в td-crm api
        :return: json от td-crm или None
        """
        method = method.format(teledomophone)
        td_request = '{}/{}'.format(self._td_api_url, method)
        result = self.__td_api_get(uuid_hdr, td_request)
        if result:
            return result

    def device_address(self, teledomophone,
                       uuid_hdr='unknown',
                       method='device/{}/address'):
        """
        Получение адреса установки теледомофона
        auth Bearer
        GET http://td-crm.is74.ru/api/device/<teledomophone>/address
        :param teledomophone: sip поле From. id вызывающего теледомофона.
        :param uuid_hdr: заголовок UUID, для сквоззного логирования вызова
        :param method: метод вызываемый в td-crm api
        :return: json от td-crm или None
        """
        method = method.format(teledomophone)
        td_request = '{}/{}'.format(self._td_api_url, method)
        result = self.__td_api_get(uuid_hdr, td_request)
        if result:
            return result

    def get_accaunt_fias(self, fias_id, flat_id,
                         uuid_hdr='unknown',
                         method='sip/fias/{}:{}'):
        """
        Метод возвращает список sip-аккаунтов привязанных к квартире(flat_id)
        в доме, определённому по fias_id
        Используется в работе с калитками при распознавании адреса и дальнейшего резолвинга
        auth Bearer
        GET http://td-crm.is74.ru/api/sip/fias/<fias_id>:<flat_id>
        :param fias_id: id в ФИАС (Федеральная информационная адресная система)
        :param flat_id: id квартиры ??? ФИАС-id или просто её номер ???
        :param uuid_hdr: заголовок UUID, для сквоззного логирования вызова
        :param method: метод вызываемый в td-crm api
        :return: json от td-crm или None
        """
        method = method.format(fias_id, flat_id)
        td_request = '{}/{}'.format(self._td_api_url, method)
        result = self.__td_api_get(uuid_hdr, td_request)
        if result:
            return result

