import os
import sys

# add root directory to python path
ROOT_PATH = os.path.dirname(__file__) + '/../'
sys.path.append(os.path.abspath(ROOT_PATH))

from twisted.application import service, internet
from twisted.internet import ssl
from twisted.web import static, server, util

from config.config import Config
config = Config()

def getWebService():
    key_path = config.get_ssl_key_path()
    cert_path = config.get_ssl_cert_path()
    ssl_context = ssl.DefaultOpenSSLContextFactory(key_path, cert_path)

    webapp_port = int(config.get_environment_web_port())
    webapp_server = server.Site(static.File(os.path.abspath(ROOT_PATH + '/webapp')))
    return internet.SSLServer(webapp_port, webapp_server, ssl_context)

def getHTTPRedirect():
    redirect_port = int(config.get_environment_http_redirect_port())
    if not redirect_port:
        return

    host = config.get_environment_host()
    webapp_port = config.get_environment_web_port()
    redirect_url = host + ':' + webapp_port
    redirect_server = server.Site(util.Redirect(redirect_url))
    return internet.TCPServer(redirect_port, redirect_server)


application = service.Application("GARPR webapp")

# attach the service to its parent application
webapp_service = getWebService()
webapp_service.setServiceParent(application)

redirect_service = getHTTPRedirect()
if redirect_service:
    redirect_service.setServiceParent(application)
