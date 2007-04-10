from zope.interface import Interface 
from zope.configuration.fields import GlobalObject
from zope.schema import TextLine
from opencore.redirect import global_defaulthost
from opencore.redirect.interfaces import IDefaultHost as IDefaultHostDirective


def set_default_host(host, path):
    global_default_host.host=host
    global_default_host.path=path

    
def configure_default_host(_context, host, path, zcml=True):
    _context.action(
        # if more than one DH is registered, will raise conflict
        # warning. can be overridden
        discriminator = 'opencore.redirect.default_host already registered',
        callable = set_default_host,
        args = (host, path)
        )
    
