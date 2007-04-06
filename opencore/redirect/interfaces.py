from zope.interface.common.mapping import IReadMapping, IWriteMapping
from zope.interface import Interface, Attribute, implements
from zope.schema import TextLine

HOOK_NAME = '__redirection_hook__'

try:
    from zope.annotation.interfaces import IAnnotatable
except ImportError:
    from zope.app.annotation.interfaces import IAnnotatable
    

class IRedirected(IAnnotatable):
    """An object that submits to selective redirection traversal"""


class INotRedirected(Interface): 
    """An object that is ignored by the redirector under all circumstances"""


class IRedirectInfo(IReadMapping, IWriteMapping):
    """Redirect annotation BTree bag"""
    url = Attribute('base url for redirection')
    parent = Attribute('physical path to a parent object')


class IDefaultHost(Interface):
    """utility declaratively representing the default host for an
    instance('opencore.redirect.default_host')"""
    host = TextLine(
        title=u"Default Host", 
        description=u"The hostname to default to")

    path = TextLine(
        title=u"Default Path Prefix", 
        description=u"The default path to prepend to the object",
        required=False
        )


class IRedirectEvent(Interface):
    request = Attribute('current request')
    obj = Attribute('current traversed object')


class RedirectEvent(object):
    implements(IRedirectEvent)
    def __init__(self, obj, request):
        self.obj = obj
        self.request = request


class ITestObject(Interface):
    # @@ remove when problem gets fixed
    """because for some reason, no default view is regged for folders in ZTC"""


class IRedirectSetup(Interface): 
    
    redirect_url = TextLine(
        title = u'Redirect URL', 
        required = True, 
        description = u'redirect to this url')
    



