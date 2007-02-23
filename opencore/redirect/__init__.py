from BTrees.OOBTree import OOBTree
from Products.Five import BrowserView
from Products.Five.traversable import FiveTraversable
from memojito import memoizedproperty
from opencore.redirect.interfaces import IRedirected, IRedirectInfo
from persistent.list import PersistentList
from zope.component import getMultiAdapter, adapts
from zope.interface import implements, alsoProvides
from zope.app.traversing.adapters import Traverser, _marker
from zope.app.traversing.interfaces import ITraverser

try:
    from zope.annotation.interfaces import IAnnotations, IAnnotatable
except ImportError:
    from zope.app.annotation.interfaces import IAnnotations

import logging


_marker = object()
LOG = KEY = "opencore.redirect"


class RedirectInfo(OOBTree):
    implements(IRedirectInfo)

    def __init__(self, url=None, parent=None):
        super(RedirectInfo, self).__init__()
        self.url = url
        self.parent = parent


def get_annotation(obj, key, **kwargs):
    ann = IAnnotations(obj)
    notes = ann.get(key)
    if not notes and kwargs:
        factory = kwargs.pop('factory')
        if not factory:
            raise Exception("No annotation factory given")
        ann[key] = factory(**kwargs)
        notes = ann[key]
    return notes


class SelectiveRedirectTraverser(Traverser):
    """if a path matches a criterion, check agains mapping, and redirect if necessary"""
    adapts(IRedirected)
    implements(ITraverser)

    @memoizedproperty
    def info(self):
        return get_annotation(self.context, KEY)
    
    def traverse(self, path, default=_marker, request=None):
        if self.info.url:
            obj = getMultiAdapter((self.info, request), name=KEY)
            return obj
        return Traverser.traverse(self, path, default=_marker, request=request)


class Redirector(BrowserView, FiveTraversable):
    redirect_url = None
    store = None
    subpath = []
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def redirect_url(self):
        return self.context.url

    @property
    def url(self):
        return "%s/%s" %(self.redirect_url, '/'.join(self.subpath))
        
    def redirect(self):
        self.request.RESPONSE.redirect(self.url)
        self.logger.info("Redirected to %s" %self.url)
        return self.request.RESPONSE

    def traverse( self, name, furtherPath ):
        # slurp path
        while furtherPath:
            self.subpath.append( furtherPath.pop( 0 ) )
        return self
    
    @property
    def logger(self):
        return logging.getLogger(LOG)


def apply_redirect(obj, url=None, parent=None, subprojects=None):
    alsoProvides(obj, IRedirected)
    info = get_annotation(obj, KEY, factory=RedirectInfo, url=url, parent=parent)
    if subprojects:
        for project_name, path in subprojects:
            info[project_name] = path
    return info

def get_redirect_info(obj):
    if IRedirected.providedBy(obj):
        return get_annotation(obj, KEY)
    raise TypeError('Object does not provide %s' %IRedirected)
    
def remove_subproject(obj, ids):
    info= get_annotation(obj, KEY, factory=RedirectInfo, url=url, parent=parent)
    for pid in ids:
        if info.get(pid):
            del info[pid]
