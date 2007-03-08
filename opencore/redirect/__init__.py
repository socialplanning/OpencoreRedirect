from BTrees.OOBTree import OOBTree
from Products.Five import BrowserView
from Products.Five.traversable import Traversable
from memojito import memoizedproperty
from opencore.redirect.interfaces import IRedirected, IRedirectInfo
from persistent.mapping import PersistentMapping
from persistent import Persistent
from zope.component import getMultiAdapter, adapts
from zope.interface import implements, alsoProvides

from Products.OpenPlans.interfaces import IProject 

try:
    from zope.interface import noLongerProvides
except ImportError:
    from Products.Five.utilities.marker import erase as noLongerProvides
from zope.app.traversing.adapters import Traverser, _marker
from zope.app.traversing.interfaces import ITraverser
from five.intid.keyreference import get_root
from opencore.redirect.classproperty import property as kproperty

try:
    from zope.annotation.interfaces import IAnnotations, IAnnotatable
except ImportError:
    from zope.app.annotation.interfaces import IAnnotations

import logging


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

class DefaultingRedirectTraverser(Traverser): 
    """
    this object redirects to a default url for 
    any IProject which has not had an explicit 
    redirection url set. 
    """

    adapts(IProject)
    implements(ITraverser)

    @memoizedproperty 
    def default_host(self): 
        # XXX this is a hack ! 
        return "http://localhost:8080"

    def default_url_for(self, object, request): 
        # XXX this is a hack ! 
        return "http://localhost:8080/normal_redirect"

    _default_traverse=Traverser.traverse

    def traverse(self, path, default=_marker, request=None): 
        server_url = request.get('SERVER_URL')

        if not server_url.startswith(self.default_host): 
            self.logger.info("Defaulting Redirector: redirecting request for %s (not under %s)" % (server_url, self.default_host))
            redirector = getMultiAdapter((self.context, request), name=KEY)
            redirector.redirect_url = self.default_url_for(self.context, request)
            seg = path[0]
            if seg in request['PATH_INFO']: 
                redirector.path_start = seg 
            return redirector 
        else: 
            self.logger.info("Defaulting Redirector: skipping request for %s (under %s)" % (server_url, self.default_host))
            return self._default_traverse(path, default=_marker, request=request)

    @property
    def logger(self):
        return logging.getLogger(LOG)
        

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
        context_path = self.context_path
        url_path = self.url_path 

        cp_len = len(context_path)
        rest = url_path[cp_len:]

        if url_path[:cp_len] != context_path: 
            # if the url_path does not start with the context_path 
            # the context object has not been reached using 
            # its physical path... 
            #
            # here we assume it has been reached by a longer 
            # url than its physical url by searching for 
            # the objects name in the remainder of the 
            # url_path, which is somewhat questionable
            # (might it not be the first instance of the name 
            #  in the list?) 
            #
            # we allow ValueError to be raised here if the 
            # object's name is not present in the remainder 
            # because we have no sensible choice to make 
            # otherwise...

            ob_name = context_path[-1]
            ob_pos = rest.index(ob_name)
            rest = rest[ob_pos+1:]
            
        # if 'redirect' has been placed on the url_path by traversal 
        # hackishly, don't include it. 
        if self.request._hacked_path and len(rest) > 0 and rest[-1] == 'redirect': 
            return rest[:-1]
        else:
            return rest

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
