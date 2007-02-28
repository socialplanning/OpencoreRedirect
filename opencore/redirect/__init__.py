from BTrees.OOBTree import OOBTree
from Products.Five import BrowserView
from Products.Five.traversable import Traversable
from memojito import memoizedproperty
from opencore.redirect.interfaces import IRedirected, IRedirectInfo
from persistent.list import PersistentList
from zope.component import getMultiAdapter, adapts
from zope.interface import implements, alsoProvides
try:
    from zope.interface import noLongerProvides
except ImportError:
    from Products.Five.utilities.marker import erase as noLongerProvides
from zope.app.traversing.adapters import Traverser, _marker
from zope.app.traversing.interfaces import ITraverser
from five.intid.keyreference import get_root

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

from cStringIO import StringIO

out = StringIO()

class SelectiveRedirectTraverser(Traverser):
    """if a path matches a criterion, check agains mapping, and redirect if necessary"""
    adapts(IRedirected)
    implements(ITraverser)

    debug = False
    get_root = staticmethod(get_root)
    _default_traverse=Traverser.traverse

    @memoizedproperty
    def info(self):
        return get_annotation(self.context, KEY)

    def reroute(self, path, default=_marker):
        reroute = self.info.get(path)
        if reroute:
            return self.get_root(self.context).restrictedTraverse(reroute)
        return default

    def traverse(self, path, default=_marker, request=None):
        server_url = request.get('SERVER_URL')

        # check for external redirect
        if self.info.url and not server_url.find(self.info.url)>-1:
            obj = getMultiAdapter((self.info, request), name=KEY)
            obj.path_start = path.pop()
            return obj

        # check for internal redirect
        obj = self.reroute(path[0])
        if obj is not _marker:
            return obj

        # traverse normally
        return self._default_traverse(path, default=_marker, request=request)


class Redirector(BrowserView, Traversable):
    """there is only zpublisher"""
    implements(ITraverser)
    debug = False
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.store = None
        self.subpath = []
        self.path_start = None

    @property
    def redirect_url(self):
        return self.context.url

    @property
    def url(self):
        return "%s/%s/%s" %(self.redirect_url,
                            self.path_start,
                            '/'.join(self.subpath))
        
    def redirect(self):
        self.request.RESPONSE.redirect(self.url)
        self.logger.info("Redirected to %s" %self.url)
        return self.request.RESPONSE

    #@@ 2.10?:: def traverse( self, name, furtherPath ):
    def traverse(self, path, default=_marker, request=None):
        self.subpath.append(path[0])
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

activate = apply_redirect

def deactivate(obj):
    noLongerProvides(obj, IRedirected)

def get_redirect_info(obj):
    if IRedirected.providedBy(obj):
        return get_annotation(obj, KEY)
    raise TypeError('Object does not provide %s' %IRedirected)

    
def remove_subproject(obj, ids):
    info= get_annotation(obj, KEY, factory=RedirectInfo, url=url, parent=parent)
    for pid in ids:
        if info.get(pid):
            del info[pid]
