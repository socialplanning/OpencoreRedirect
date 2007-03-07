from BTrees.OOBTree import OOBTree
from Products.Five import BrowserView
from Products.Five.traversable import Traversable
from five.intid.keyreference import get_root
from memojito import memoizedproperty
from opencore.redirect.classproperty import property as kproperty
from opencore.redirect.interfaces import IRedirected, IRedirectInfo
from persistent import Persistent
from persistent.mapping import PersistentMapping
from zope.app.traversing.adapters import Traverser, _marker
from zope.app.traversing.interfaces import ITraverser
from zope.component import getMultiAdapter, adapts
from zope.interface import implements, alsoProvides
import logging

try:
    from zope.annotation.interfaces import IAnnotations, IAnnotatable
except ImportError:
    from zope.app.annotation.interfaces import IAnnotations

try:
    from zope.interface import noLongerProvides
except ImportError:
    from Products.Five.utilities.marker import erase as noLongerProvides



_marker = object()
LOG = KEY = "opencore.redirect"
RESERVED_PREFIX = "opencore_redirect"

class RedirectInfo(PersistentMapping):
    implements(IRedirectInfo)
    def __init__(self, url=None, parent=None):
        super(RedirectInfo, self).__init__()
        self.url = url
        self.parent = parent
        self._p_changed=1
        
    def __repr__(self):
        return "%s -> '%s' => %s" %(Persistent.__repr__(self),
                                    self.url,
                                    super(RedirectInfo, self).__repr__())


class SelectiveRedirectTraverser(Traverser):
    """if a path matches a criterion, check agains mapping, and redirect if necessary"""
    adapts(IRedirected)
    implements(ITraverser)

    debug = False
    get_root = staticmethod(get_root)
    _default_traverse=Traverser.traverse

    @property
    def logger(self):
        return logging.getLogger(LOG)

    @memoizedproperty
    def info(self):
        info = get_annotation(self.context, KEY)
        return info

    def reroute(self, path, default=_marker):
        reroute = self.info.get(path)
        if reroute:
            return self.get_root(self.context).restrictedTraverse(reroute)
        return default

    def traverse(self, path, default=_marker, request=None):
        server_url = request.get('SERVER_URL')
        
        # check for external redirect
        if (self.info.url and not server_url.find(self.info.url)>-1
            and not path[0].startswith(RESERVED_PREFIX) and 
            not RESERVED_PREFIX in request.getURL()):
            obj = getMultiAdapter((self.context, request), name=KEY)
            obj.redirect_url = self.info.url
            seg = path[0]
            if seg in request['PATH_INFO']:
                obj.path_start = seg
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

    def __of__(self, obj):
        if obj is self:
            return self
        return super(Redirector, self).__of__(obj)

    @property
    def context_path(self):
        return list(self.context.getPhysicalPath())

    @property
    def url_path(self):
        return self.request.physicalPathFromURL(self.request.getURL())

    @property
    def further_path(self):
        less = len(self.context_path)
        fp = self.url_path[less:]
        if self.request._hacked_path and len(fp) > 0 and fp[-1] == 'redirect': 
            return fp[0:-1]
        else:
            return fp

    class redirect_url(kproperty):
        def fget(self):
            return "%s/%s" %(self._url, '/'.join(self.further_path))
        def fset(self, value):
            self._url = value
        
    def redirect(self):
        if getattr(self.request, "__redirected__", False):
            return

        self.request.RESPONSE.redirect(self.redirect_url)
        self.logger.info("Redirected to %s" %self.redirect_url)
            
        self.request.__redirected__=True 
        return self.request.RESPONSE

    #@@ 2.10?:: def traverse( self, name, furtherPath ):
    def traverse(self, path, default=_marker, request=None):
        self.subpath.append(path[0]) # necessary?
        return self
    
    @property
    def logger(self):
        return logging.getLogger(LOG)


def apply_redirect(obj, url=None, parent=None, subprojects=None):
    alsoProvides(obj, IRedirected)
    info = get_annotation(obj, KEY, factory=RedirectInfo, url=url, parent=parent)
    if info.url is not url:
        info.url = url
    if info.parent is not parent:
        info.parent = parent
    if subprojects:
        for project_name, path in subprojects:
            info[project_name] = path
    info._p_changed=1
    return info

activate = apply_redirect


def deactivate(obj):
    noLongerProvides(obj, IRedirected)


def get_redirect_info(obj):
    if IRedirected.providedBy(obj):
        return get_annotation(obj, KEY)
    raise TypeError('Object does not provide %s' %IRedirected)

get_info = get_redirect_info

    
def remove_subproject(obj, ids):
    info= get_annotation(obj, KEY, factory=RedirectInfo, url=url, parent=parent)
    for pid in ids:
        if info.get(pid):
            del info[pid]


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
