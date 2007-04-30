from zope.interface import Interface 
from opencore.redirect import _global_default_redirect_info as redir_info
from opencore.redirect import logger
from opencore.redirect.interfaces import IDefaultRedirectHostDirective
import urlparse


def set_host_info(host, path):
    redir_info.host=host
    redir_info.ignore_path=path

def configure_default_redirect_host(_context, host, ignore_path=''):

    _context.action(
        # if more than one DH is registered, will raise conflict
        # warning. can be overridden
        discriminator = 'opencore.redirect.defaulthost already registered',

        callable = set_host_info,
        args = (host, ignore_path)
        )
