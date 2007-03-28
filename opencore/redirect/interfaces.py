from zope.interface.common.mapping import IReadMapping, IWriteMapping
from zope.interface import Interface, Attribute, implements
from zope.schema import TextLine

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
        )


class ITestObject(Interface):
    # @@ remove when problem gets fixed
    """because for some reason, no default view is regged for folders in ZTC"""


    
