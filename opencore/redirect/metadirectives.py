from zope.interface import Interface 
from zope.configuration.fields import GlobalObject
from zope.schema import TextLine


class IDefaultHostDirective(Interface): 
    """
    configures the default host used by 
    the DefaultingRedirectTraverser
    """
    
    host = TextLine(
        title=u"Default Host", 
        description=u"The hostname to default to")

    path = TextLine(
        title=u"Default Path Prefix", 
        description=u"The default path to prepend to the object",
        )

    for_ = GlobalObject(
        title=u"For Class", 
        description=u"The class to set default redirect info on.")

    layer = TextLine(
        title=u"Layer", 
        description=u"The layer the configuration is defined in",
        required=False)
