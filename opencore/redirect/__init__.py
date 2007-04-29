from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem
from hook import AccessEventHook, enableAccessEventHook, disableAccessEventHook
from memojito import memoizedproperty
from opencore.redirect.classproperty import property as classproperty
from opencore.redirect.interfaces import IRedirectEvent, RedirectEvent, HOOK_NAME
from opencore.redirect.interfaces import IRedirectInfo, IHostInfo
from opencore.redirect.interfaces import IRedirected, INotRedirected
from opencore.redirect.interfaces import RedirectActivationEvent, RedirectDeactivationEvent
from opencore.redirect.interfaces import IRedirectManagementEvent
from persistent import Persistent
from persistent.mapping import PersistentMapping
from zope import event
from zope.app.component import queryNextUtility
from zope.app.traversing.adapters import Traverser, _marker
from zope.app.traversing.interfaces import ITraverser
from zope.component import getMultiAdapter, adapts, adapter
from zope.component import getUtility, handle
from zope.interface import implements, alsoProvides, Interface
import logging
import urlparse

try:
    from zope.interface import noLongerProvides
except ImportError:
    from Products.Five.utilities.marker import erase as noLongerProvides

try:
    from zope.annotation.interfaces import IAnnotations, IAnnotatable
except ImportError:
    from zope.app.annotation.interfaces import IAnnotations


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
    def __init__(self, defhost='', defpath=''):
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
        
        def fset(self, host):
            if host and not urlparse.urlparse(host)[0]:
                logger.warn("no scheme specified in default host '%s' assuming http" % host)
                host = 'http://%s' % host

            self._host = host
    
# == subscribers == #

def redispatch(event):
    handle(event.obj, event)

@adapter(IRedirectEvent)
def log_redirect_event(event):
    logger.info("%s -- %s" %(event.request.getURL(), event.obj))

@adapter(IRedirectManagementEvent)
def log_redirect_management_event(event):
    logger.info("%s -- %s" %(event, event.obj))

def hosts_match(url1, url2):
    return urlparse.urlparse(url1)[1] == urlparse.urlparse(url2)[1]


@adapter(IRedirected, IRedirectEvent)
def explicit_redirection(obj, event):
    request=event.request
    if should_ignore(obj, request):
        raise RuntimeError("we should not be here")
        
    server_url = request.get('SERVER_URL')
    redirect_server = None
    info = get_annotation(obj, KEY)

    # check for external redirect
    if (info.url and not hosts_match(server_url, info.url)
        and not RESERVED_PREFIX in request['PATH_INFO'] and 
        not RESERVED_PREFIX in request.getURL()):
        do_relative_redirect(request, info.url)

# @@ consider stacking event ie. make this listener before
# redispatching
@adapter(Interface, IRedirectEvent)
def defaulting_redirection(obj, event):
    if IRedirected.providedBy(obj):
        return False # bail out
    request=event.request
    server_url = request.get('SERVER_URL')
    default_host, path = get_host_info()
    
    if (not should_ignore(obj, request) and 
        (default_host and 
         not hosts_match(server_url, default_host))):
        
        logger.info("DF: redirecting request "
                         "for %s (not under %s)" % (request['ACTUAL_URL'], default_host))

        base_url = default_url_for(obj, default_host, path=path)
        if base_url is not None:
            return do_relative_redirect(request, base_url)


def default_url_for(object, default_host, path=""):
    """
    returns default_host/default_path/object_id 
    """
    assert('://' in default_host) 
    
    url = default_host
    if path:
        url = urlparse.urljoin(url, path)
        if not url.endswith('/'):
            url += '/'
                    
    url = urlparse.urljoin(url, object.id)    
    logger.info("Default URL for %s is %s" % (object, url))
    return url

def do_relative_redirect(request, base_url):
    """
    redirect the remaining portion of the request
    (the request.path stack and query args)
    relative to base_url.
    """
    
    assert('://' in base_url) 

    rest = request.path[:]
    rest.reverse()
    rest = '/'.join(rest)
    url = base_url
    if not url.endswith('/'):
        url += '/'
    url = urlparse.urljoin(url, rest)

    qs = request['QUERY_STRING']
    if qs:
        url += '?%s' % qs 

    request.RESPONSE.redirect(url, lock=1)
    logger.info("Set redirect location to %s" % url)

def get_host_info():
    host_info = getUtility(IHostInfo)
    return host_info.host, host_info.path


# == hook functions == #

class RedirectHook(AccessEventHook):
    event = RedirectEvent


def enableRedirectHook(obj):
    enableAccessEventHook(obj, hook_class=RedirectHook, hook_name=HOOK_NAME)


def disableRedirectHook(obj):
    disableAccessEventHook(obj, HOOK_NAME)
    

# == convenience functions == #

def activate(obj, url=None, parent=None, subprojects=None, explicit=True):

    if url and not urlparse.urlparse(url)[0]:
        logger.warn("no scheme specified in redirect host '%s' assuming http" % url)
        url = 'http://%s' % url
    
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
    event.notify(RedirectActivationEvent(obj))
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
    event.notify(RedirectDeactivationEvent(obj))


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




def should_ignore(ob, request):
    # if the object is explicitly tagged as INotRedirected
    # always ignore it. Also ignore if the object is
    # not being published(denoted by existence of '_post_traverse').
    publishing = hasattr(request, '_post_traverse')
    if INotRedirected.providedBy(ob) or not publishing:
        return True
    return False
