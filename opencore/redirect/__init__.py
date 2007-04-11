from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem
from Products.Five import BrowserView
from Products.Five.traversable import Traversable
from memojito import memoizedproperty
from opencore.redirect.interfaces import IRedirected, INotRedirected, \
     IRedirectInfo, IHostInfo
from opencore.redirect.interfaces import IRedirectEvent, RedirectEvent, HOOK_NAME
from persistent.mapping import PersistentMapping
from persistent import Persistent
from zope.component import getMultiAdapter, adapts, adapter
from zope.component import getUtility, handle
from zope.interface import implements, alsoProvides, Interface
from hook import AccessEventHook, enableAccessEventHook, disableAccessEventHook
import urlparse 

try:
    from zope.interface import noLongerProvides
except ImportError:
    from Products.Five.utilities.marker import erase as noLongerProvides
from zope.app.traversing.adapters import Traverser, _marker
from zope.app.traversing.interfaces import ITraverser
from five.intid.keyreference import get_root
from opencore.redirect.classproperty import property as classproperty
from zope.app.component import queryNextUtility

try:
    from zope.annotation.interfaces import IAnnotations, IAnnotatable
except ImportError:
    from zope.app.annotation.interfaces import IAnnotations

import logging


_marker = object()
LOG = KEY = "opencore.redirect"
RESERVED_PREFIX = "opencore_redirect"
logger = logging.getLogger(LOG)

# == annotation bag == #

class RedirectInfo(PersistentMapping):
    implements(IRedirectInfo)
    def __init__(self, url=None, parent=None):
        super(RedirectInfo, self).__init__()
        self.url = url
        self.parent = parent
        self._p_changed = 1
        
    def __repr__(self):
        return "%s -> '%s' => %s" %(Persistent.__repr__(self),
                                    self.url,
                                    super(RedirectInfo, self).__repr__())

# == utility == #

class HostInfo(object):
    implements(IHostInfo)
    def __init__(self, defhost='http://localhost:8080', defpath=''):
        self.path = defpath
        self.host = defhost

_global_host_info = HostInfo()


class LocalHostInfo(SimpleItem):
    implements(IHostInfo)
    def __init__(self, defhost='', defpath=''):
        self._path = defpath
        self._host = defhost

    def fetch(attr, val=None, cur_dh=None):
        if val: return val
        if not cur_dh:
            self = cur_dh
        cur_dh = queryNextUtility(cur_dh, IHostInfo)
        if not cur_dh:
            return ''
        return self.fetch(attr, getattr(cur_dh, attr, None), cur_dh)

    class path(classproperty):
        def fget(self):
            if self._path:
                return self._path
            return self.fetch('path')
            
        def fset(self, val):
            self._path = val

    class host(classproperty):
        def fget(self):
            if self._host:
                return self._host
            return self.fetch('host')
        
        def fset(self, val):
            self._host = val
    
# == subscribers == #

@adapter(IRedirectEvent)
def notify_redirect_event(event):
    handle(event.obj, event)
    
@adapter(IRedirectEvent)
def log_redirect_event(event):
    logger.info("%s -- %s" %(event.request.getURL(), event.obj))

@adapter(IRedirected, IRedirectEvent)
def explicit_redirection(obj, event):
    request=event.request
    if should_ignore(obj, request):
        raise RuntimeError("we should not be here")
        
    server_url = request.get('SERVER_URL')
    redirect_server = None
    info = get_annotation(obj, KEY)
    if info.url: 
        redirect_server = urlparse.urlparse(info.url)[1]

    # check for external redirect
    if (redirect_server and not server_url.find(redirect_server)>-1
        and not RESERVED_PREFIX in request['PATH_INFO'] and 
        not RESERVED_PREFIX in request.getURL()):
            
        set_redirect(obj, request, info.url)

# @@ consider stacking event ie. make this listener before
# redispatching
@adapter(Interface, IRedirectEvent)
def defaulting_redirection(obj, event):
    if IRedirected.providedBy(obj):
        return False # bail out
    request=event.request
    host_info = getUtility(IHostInfo)
    default_host = host_info.host
    path = host_info.path
    server_url = request.get('SERVER_URL')
    if not should_ignore(obj, request) and \
           (default_host and not server_url.startswith(default_host)):
        
        logger.info("DF: redirecting request "
                         "for %s (not under %s)" % (server_url, default_host))

        #@@ def url fuxored?
        new_url = default_url_for(default_host, obj, request, default_path=path)
        if new_url is not None:
            return set_redirect(obj, request, new_url)


# == traversers == #

class SubitemSpoofingTraverser(Traverser):
    get_root = staticmethod(get_root)
    _default_traverse = Traverser.traverse

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
        # check for internal redirect
        obj = self.reroute(path[0])
        if obj is not _marker:
            return obj

        # if none found traverse normally @@ not respecting default
        # traversal as primary might be a 'crime against nature'
        return self._default_traverse(path, default=_marker, request=request)




# == view == #

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
    def original_url(self):
        return "%s%s" %(self.request['SERVER_URL'], self.request['PATH_INFO'])

    @property
    def url_path(self):
        return self.request.physicalPathFromURL(self.original_url)

    @property
    def further_path(self):
        context_path = self.context_path
        url_path = self.url_path 

        cp_len = len(context_path)
        rest = url_path[cp_len:]

##         if url_path[:cp_len] != context_path: 
##             # XXX 
##             #
##             # if the url_path does not start with the context_path 
##             # the context object has not been reached using 
##             # its physical path... 
##             #
##             # here we assume it has been reached by a longer 
##             # url than its physical url by searching for 
##             # the objects name in the remainder of the 
##             # url_path, which is somewhat questionable
##             # (might it not be the first instance of the name 
##             #  in the list?) 
##             #
##             # we allow ValueError to be raised here if the 
##             # object's name is not present in the remainder 
##             # because we have no sensible choice to make 
##             # otherwise...
##             #
##             # now if getPhysicalPathFromURL could actually return 
##             # the kind of path that context.getPhysicalPath does, 
##             # we'd be in better shape... we could simply strip 
##             # off the prefix context_path from url_path 
##             #
##             ob_name = context_path[-1]
##             ob_pos = rest.index(ob_name)
##             rest = rest[ob_pos+1:]
            
        # if 'redirect' has been placed on the url_path by traversal 
        # hackishly, don't include it. 
        if self.request._hacked_path and len(rest) > 0 and \
               rest[-1] == 'redirect':
            self.logger.info("hacked path:%s")
            return rest[:-1]
        else:
            return rest

    class redirect_url(classproperty):
        def fget(self):
            return "%s/%s" %(self._url, '/'.join(self.further_path))
        def fset(self, value):
            self._url = value
        
    def redirect(self):
        self.request.RESPONSE.redirect(self.redirect_url, lock=1)
        self.logger.info("Redirected to %s" %self.redirect_url)
        return self.request.RESPONSE

    #@@ 2.10?:: def traverse( self, name, furtherPath ):
    def traverse(self, path, default=_marker, request=None):
        self.subpath.append(path[0]) # necessary?
        return self
    
    @property
    def logger(self):
        return logging.getLogger(LOG)


# == hook functions == #

class RedirectHook(AccessEventHook):
    event = RedirectEvent


def enableRedirectHook(obj):
    enableAccessEventHook(obj, hook_class=RedirectHook, hook_name=HOOK_NAME)


def disableRedirectHook(obj):
    disableAccessEventHook(obj, HOOK_NAME)
    

# == convenience functions == #

def activate(obj, url=None, parent=None, subprojects=None, explicit=True):
    if explicit:
        alsoProvides(obj, IRedirected)
    info = get_annotation(obj, KEY, factory=RedirectInfo, url=url,
                          parent=parent)
    if info.url is not url:
        info.url = url
    if info.parent is not parent:
        info.parent = parent
    if subprojects:
        for project_name, path in subprojects:
            info[project_name] = path
    info._p_changed=1
    enableRedirectHook(obj)
    #@@ notify here?
    return info

apply_redirect = activate


def get_redirect_url(obj):
    try:
        return getattr(get_redirect_info(obj), 'url', None)
    except TypeError:
        return None


def deactivate(obj, disable_hook=False):
    noLongerProvides(obj, IRedirected)
    if disable_hook:
        disableRedirectHook(obj)
    #@@ notify here?

def get_info(obj):
    return get_annotation(obj, KEY)

get_redirect_info = get_info

    
def remove_subproject(obj, ids):
    info= get_annotation(obj, KEY, factory=RedirectInfo, url=url,
                         parent=parent)
    for pid in ids:
        if info.get(pid):
            del info[pid]
            

# == helpers == #

def pathstr(zope_obj):
    path = zope_obj.getPhysicalPath()
    return '/'.join(path)


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


def set_redirect(context, request, url, path_start=None):
    redirector = getMultiAdapter((context, request), name=KEY)
    redirector.redirect_url = url
    if path_start:
        redirector.path_start=path_start
    redirector.redirect()


def should_ignore(ob, request): 
    # if the object is explicitly tagged as INotRedirected 
    # always ignore it. Also ignore if the object is 
    # not being published(denoted by existence of '_post_traverse').
    publishing = hasattr(request, '_post_traverse')
    if INotRedirected.providedBy(ob) or not publishing: 
        return True
    return False


def default_url_for(default_host, object, request, default_path=""):
    """
    """
    if default_host is None: 
        return None

    url = '/'.join([x for x in default_host, default_path, object.getId(), if x])
    
    logger.info("Default URL for %s is %s" % (object, url))

    return url


