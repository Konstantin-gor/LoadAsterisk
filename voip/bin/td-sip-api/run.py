# -*- coding: utf-8 -*-
from api import app, api_host, api_port

if __name__ == '__main__':
    app.run(debug=False, host=api_host, port=api_port)
