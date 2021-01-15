#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymysql
from sys import path
import logging

class Mysql:
    __log = logging.getLogger()
    
    def __init__(self, **kwargs):

        self.mysql_user = kwargs.get('user')
        self.mysql_password = kwargs.get('password')
        self.mysql_host = kwargs.get('host')
        self.mysql_db = kwargs.get('shema')
        self.__log.debug("собрали переменные для подключения к MySql")

    def connect(self):
        self.mysql_connect  = pymysql.Connection(self.mysql_host, self.mysql_user, self.mysql_password, self.mysql_db, autocommit=True)
        if self.mysql_connect:
            self.__log.debug("подключились к Mysql, хост {0!r}, отдаем курсор под пользователем {1!r} в схему {2!r}".format(self.mysql_host, self.mysql_user, self.mysql_db))
            self.mysql_cursor = self.mysql_connect.cursor()
        else:
            self.__log.debug("не удалось подключиться к Mysql")
            self.mysql_cursor = False
        return self.mysql_cursor

    def disconnect(self):
        if self.mysql_cursor:
            self.mysql_cursor.close()
            self.__log.debug("Удалил курсор Mysql")
        self.mysql_connect.close()
        self.__log.debug("Закрыли коннект с Mysql")

    def execute(self, s, args=None):
        mysql_cursor = self.connect()
        if mysql_cursor:
            self.__log.debug("Выполняем запрос {} с параметрами {}".format(s, args))
            mysql_cursor.execute(s, args)
        if mysql_cursor:
            result_list = []
            for row in mysql_cursor:
                result_list.append(row)
        self.disconnect()
        return tuple(result_list)

    def callproc(self, s, args=None):
        mysql_cursor = self.connect()
        if mysql_cursor:
            self.__log.debug("выполняем процедуру {} с параметрами {}".format(s, args))
            mysql_cursor.callproc(s, args)

        if mysql_cursor:
            result_list = []
            for row in mysql_cursor:
                result_list.append(row)
        self.disconnect()
        return tuple(result_list)

class Oracle:
    __log = logging.getLogger()

    def __init__(self, **kwargs):
        # Параметры соединения с сервером Oracle.
        self.db_ora_user = kwargs.get('user')
        self.db_ora_password = kwargs.get('password')
        self.db_ora_tns = kwargs.get('tns')
        db_ora_tns_admin = kwargs.get('tns_admin')
        db_ora_home = kwargs.get('oracle_home')
        nls_lang = kwargs.get('nls_lang')
        os.environ["TNS_ADMIN"] = db_ora_tns_admin
        os.environ["ORACLE_HOME"] = db_ora_home
        os.environ["NLS_LANG"] = nls_lang
        self.__log.debug("собрали переменные для подключения к Oracle")

    def connect(self):
        self.connect = cx_Oracle.connect(self.db_ora_user, self.db_ora_password, self.db_ora_tns)
        if self.connect:
            self.__log.debug("подключились к Oracle, отдаем курсор под пользователем {0!r}, в БД {1!r}".format(self.db_ora_user,
                                                                                                self.db_ora_tns))
            self.cursor = self.connect.cursor()
        else:
            self.__log.debug("Не удалось подключиться к Oracle, отдаем курсор под пользователем {0!r}, в БД {1!r}".format(self.db_ora_user,
                                                                                                self.db_ora_tns))
            self.cursor = False
        return self.cursor

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
            self.__log.debug("закрыли курсор Oracle")
        self.connect.close()
        self.__log.debug("закрыли соединение с Oracle")

    def execute(self, s, args=None):
        ora_cursor = self.connect()
        self.__log.debug("выполняем запрос {0!r}с параметрами {}".format(s, args))
        if ora_cursor:
            result = ora_cursor.execute(s, args)
            result_list = []
            for row in result:
                result_list.append(row) 
        self.disconnect()
        return tuple(result_list)