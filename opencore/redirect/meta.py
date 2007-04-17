from zope.interface import Interface 
from opencore.redirect import _global_host_info as host_info
from opencore.redirect.interfaces import IHostInfo as IHostInfoDirective


def set_host_info(host, path, vhost):
    host_info.host=host
    host_info.path=path
    host_info.vhost=vhost

    
def configure_host_info(_context, host, path, vhost):
    _context.action(
        # if more than one DH is registered, will raise conflict
        # warning. can be overridden
        discriminator = 'opencore.redirect.host_info already registered',
        callable = set_host_info,
        args = (host, path, vhost)
        )
    
