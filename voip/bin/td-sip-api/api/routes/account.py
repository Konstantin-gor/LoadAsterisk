# -*- coding: utf-8 -*-
from hashlib import md5
from api import mysql


query = {
    'get_user': 'select username, domain from subscriber where username = %s and domain = %s',
    'add_user': 'INSERT INTO subscriber(username, domain, password, ha1, ha1b) VALUES (%s, %s ,%s ,%s ,%s)',
    'update_user': 'UPDATE subscriber set domain=%s, password=%s, ha1=%s, ha1b=%s where username=%s',
    'delete_user': 'delete from subscriber where username = %s and domain = %s',
    'check_user': 'select username, domain from subscriber where username like %s and domain = %s'
}


def hash_passwd(user, domain, password):
    ha1_encoded = '{username}:{domain}:{password}'.format(username=user,
                                                          domain=domain,
                                                          password=password).encode('utf8')
    ha1b_encoded = '{username}@{domain}:{domain}:password'.format(username=user,
                                                                  domain=domain,
                                                                  password=password).encode('utf8')
    ha1 = md5(ha1_encoded).hexdigest()
    ha1b = md5(ha1b_encoded).hexdigest()

    return ha1, ha1b


class Account:
    def __init__(self, **kwargs):
        self.username = kwargs.get('username') or False
        self.domain = kwargs.get('domain') or False
        self.password = kwargs.get('password') or False
        self.cursor = mysql.get_db().cursor()

    def get_user(self):
        if self.username and self.domain:
            count = self.cursor.execute(query['get_user'], (self.username, self.domain))
            if count != 0:
                rv = self.cursor.fetchone()
                self.cursor.close()
                return rv
            else:
                self.cursor.close()
                return False, 404
        else:
            return False, 400

    def add_user(self):
        if self.username and self.domain and self.password:
            ha1, ha1b = hash_passwd(self.username, self.domain, self.password)
            self.cursor.execute(query['check_user'], (self.username, self.domain))
            rv = self.cursor.fetchone()
            if rv:
                return rv, 409
            else:
                self.cursor.execute(query['add_user'], (self.username, self.domain, self.password, ha1, ha1b))
                rv = self.cursor.lastrowid
                self.cursor.close()
                return {'id': rv,
                        'username': self.username,
                        'domain': self.domain}
        else:
            return False, 400

    def update_user(self):
        if self.username and self.domain and self.password:
            ha1, ha1b = hash_passwd(self.username, self.domain, self.password)
            self.cursor.execute(query['check_user'], (self.username, self.domain))
            rv = self.cursor.fetchone()
            if not rv:
                return rv, 404
            else:
                self.cursor.execute(query['update_user'], (self.domain, self.password, ha1, ha1b, self.username))
                rv = self.cursor.lastrowid
                self.cursor.close()
                return {'id': rv,
                        'username': self.username,
                        'domain': self.domain}

    def delete_user(self):
        if self.username and self.domain:
            self.cursor.execute(query['check_user'], (self.username, self.domain))
            rv = self.cursor.fetchone()
            if not rv:
                return rv, 404
            else:
                self.cursor.execute(query['delete_user'], (self.username, self.domain))
                rv = self.cursor.lastrowid
                return {'id': rv,
                        'username': self.username,
                        'domain': self.domain}
