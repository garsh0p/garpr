import os
import sys

import OpenSSL
from twisted.application import internet, service
from twisted.internet import reactor, ssl
from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site

from config.config import Config
import server

config = Config()
ROOT_PATH = os.path.dirname(__file__)

class CustomOpenSSLContextFactory(ssl.DefaultOpenSSLContextFactory):
    def __init__(self, privateKeyFileName, certificateChainFileName,
                 sslmethod=OpenSSL.SSL.SSLv23_METHOD):
        """
        @param privateKeyFileName: Name of a file containing a private key
        @param certificateChainFileName: Name of a file containing a certificate chain
        @param sslmethod: The SSL method to use
        """
        self.privateKeyFileName = privateKeyFileName
        self.certificateChainFileName = certificateChainFileName
        self.sslmethod = sslmethod
        self.cacheContext()

    def cacheContext(self):
        ctx = OpenSSL.SSL.Context(self.sslmethod)
        ctx.use_certificate_chain_file(self.certificateChainFileName)
        ctx.use_privatekey_file(self.privateKeyFileName)
        ctx.set_options(OpenSSL.SSL.OP_NO_SSLv2)
        ctx.set_options(OpenSSL.SSL.OP_NO_SSLv3)
        self._context = ctx

def getWebService():
    key_path = config.get_ssl_key_path()
    cert_path = config.get_ssl_cert_path()
    ssl_context = CustomOpenSSLContextFactory(key_path, cert_path)

    api_port = int(config.get_environment_api_port())
    api_resource = WSGIResource(reactor, reactor.getThreadPool(), server.app)
    api_server = Site(api_resource)
    return internet.SSLServer(api_port, api_server, ssl_context)


application = service.Application("GARPR webapp")

# attach the service to its parent application
api_service = getWebService()
api_service.setServiceParent(application)
