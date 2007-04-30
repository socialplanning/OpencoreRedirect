from zope.interface import Interface 
from opencore.redirect import _global_host_info as host_info
from opencore.redirect import logger
from opencore.redirect.interfaces import IHostInfo as IHostInfoDirective
import urlparse

def set_host_info(host, path):
    host_info.host=host
    host_info.path=path

    
def configure_host_info(_context, host, path):
    _context.action(
        # if more than one DH is registered, will raise conflict
        # warning. can be overridden
        discriminator = 'opencore.redirect.host_info already registered',
        callable = set_host_info,
        args = (host, path)
        )
    
