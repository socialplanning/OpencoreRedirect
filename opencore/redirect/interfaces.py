from zope.interface.common.mapping import IReadMapping, IWriteMapping
from zope.interface import Interface, Attribute

try:
    from zope.annotation.interfaces import IAnnotatable
except ImportError:
    from zope.app.annotation.interfaces import IAnnotatable
    

class IRedirected(IAnnotatable):
    """An object that submits to selective redirection traversal"""


class IRedirectInfo(IReadMapping, IWriteMapping):
    """Redirect annotation BTree bag"""
    url = Attribute('base url for redirection')
    parent = Attribute('physical path to a parent object')


class ITestObject(Interface):
    # @@ remove when problem gets fixed
    """because for some reason, no default view is regged for folders in ZTC"""
