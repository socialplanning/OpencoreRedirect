from Products.SiteAccess.AccessRule import AccessRule
from ZPublisher.BeforeTraverse import registerBeforeTraverse
from ZPublisher.BeforeTraverse import unregisterBeforeTraverse
from zope.app.publication.zopepublication import BeforeTraverseEvent
from ExtensionClass import Base
from zope.event import notify
from Acquisition import aq_base

class AccessEventHook(Base):
    event=None
    def __call__(self, container, request):
        notify(self.event(container, request))


def enableAccessEventHook(obj, hook_class, hook_name):
    """Install __before_traverse__ hook for redirection
    """
    # We want the original object, not stuff in between, and no acquisition
    obj = aq_base(obj)
    hook = AccessRule(hook_name)
    registerBeforeTraverse(obj, hook, hook_name, 1)

    # disable any existing redirection hooks
    if hasattr(obj, hook_name):
        disableAccessEventHook(obj, hook_name)
        
    setattr(obj, hook_name, hook_class())


def disableAccessEventHook(obj, hook_name):
    """Remove __before_traverse__ hook for Redirect Hook
    """
    # We want the original object, not stuff in between, and no acquisition
    obj = aq_base(obj)
    unregisterBeforeTraverse(obj, hook_name)
    if hasattr(obj, hook_name):
        delattr(obj, hook_name)






