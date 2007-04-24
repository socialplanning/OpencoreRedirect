from zope.interface.common.mapping import IReadMapping, IWriteMapping
from zope.interface import Interface, Attribute, implements
from zope.schema import TextLine, Bool

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


class IHostInfo(Interface):
    """utility declaratively representing the default host for an
    instance('opencore.redirect.default_host')"""
    host = TextLine(
        title=u"Default Host", 
        description=u"The hostname to default to",
        required=False)

    path = TextLine(
        title=u"Default Path Prefix", 
        description=u"The default path to prepend to the object path",
        required=False
        )
    
    vhost = TextLine(
        title=u"vhost url", 
        description=u"address to virtual hoster",
        required=False
        )

# == redirect management events ==#

class IRedirectManagementEvent(Interface):
    """
    Something is happening with the setting of redirection on an
    object
    """
    obj = Attribute('object redirect is being managed for')
    

class IRedirectActivationEvent(IRedirectManagementEvent):
    """redirect is activated"""


class IRedirectDeactivationEvent(IRedirectManagementEvent):
    """redirect is deactivated"""


class RedirectManagementEvent(object):
    implements(IRedirectManagementEvent)
    def __init__(self, obj):
        self.obj = obj


class RedirectActivationEvent(RedirectManagementEvent):
    """hello, we are activating redirection"""
    implements(IRedirectActivationEvent)
    

class RedirectDeactivationEvent(RedirectManagementEvent):
    implements(IRedirectDeactivationEvent)

# == redirect event == #

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
    activate = Bool(title=u"activate",
                           description=u"check to activate redirection",
                           default=False)
    
    redirect_url = TextLine(
        title = u'Redirect URL', 
        required = False, 
        description = u'redirect to this url')


    



