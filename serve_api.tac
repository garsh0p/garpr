import os
import sys

from twisted.application import internet, service
from twisted.internet import reactor, ssl
from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site

from config.config import Config
import server

config = Config()
ROOT_PATH = os.path.dirname(__file__)

def getWebService():
    key_path = config.get_ssl_key_path()
    cert_path = config.get_ssl_cert_path()
    ssl_context = ssl.DefaultOpenSSLContextFactory(key_path, cert_path)

    api_port = int(config.get_environment_api_port())
    api_resource = WSGIResource(reactor, reactor.getThreadPool(), server.app)
    api_server = Site(api_resource)
    return internet.SSLServer(api_port, api_server, ssl_context)


application = service.Application("GARPR webapp")

# attach the service to its parent application
api_service = getWebService()
api_service.setServiceParent(application)
