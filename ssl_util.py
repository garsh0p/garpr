import OpenSSL
from twisted.internet import ssl

SECURE_CIPHERS = 'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS'

class CustomOpenSSLContextFactory(ssl.DefaultOpenSSLContextFactory):
    def __init__(self, privateKeyFileName, certificateChainFileName,
                 sslmethod=OpenSSL.SSL.SSLv23_METHOD):
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
        ctx.set_cipher_list(SECURE_CIPHERS)
        self._context = ctx
