__author__ = 'administrator'
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from main import app
import ssl
import os
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()

'''
http_server = HTTPServer(WSGIContainer(app))

#for SSL with a CA cert
'''

data_dir = "c:\\"


http_server = HTTPServer(WSGIContainer(app), ssl_options={
"certfile": os.path.join(data_dir, "________"),
"keyfile": os.path.join(data_dir, "__________"),
"ssl_version": ssl.PROTOCOL_TLSv1})


#http_server.listen(80)
http_server.listen(443)
IOLoop.instance().start()