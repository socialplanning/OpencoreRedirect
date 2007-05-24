from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem
from hook import AccessEventHook, enableAccessEventHook, disableAccessEventHook
from memojito import memoizedproperty
from opencore.redirect.classproperty import property as classproperty
from opencore.redirect.interfaces import IRedirectEvent, RedirectEvent, HOOK_NAME
from opencore.redirect.interfaces import IRedirectInfo, IDefaultRedirectInfo
from opencore.redirect.interfaces import IRedirected
from opencore.redirect.interfaces import RedirectActivationEvent, RedirectDeactivationEvent
from opencore.redirect.interfaces import IRedirectManagementEvent
from persistent import Persistent
from persistent.mapping import PersistentMapping
from zope import event
from zope.app.component import queryNextUtility
from zope.app.traversing.adapters import Traverser, _marker
from zope.app.traversing.interfaces import ITraverser
from zope.component import getMultiAdapter, adapts, adapter
from zope.component import queryUtility, handle
from zope.interface import implements, alsoProvides, Interface
from zExceptions import Redirect
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
LOG = REDIRECT_ANNOTATION = "opencore.redirect"
RESERVED_PREFIX = "opencore_redirect"
logger = logging.getLogger(LOG)

# helper, but used during init
def clean_host(host):
    
    if not host:
        return ''
    
    if not '://' in host:
        logger.warn("no scheme specified in host '%s' assuming http" % host)
        host = 'http://%s' % host

    return host

# == annotation bag == #

class RedirectInfo(PersistentMapping):
    implements(IRedirectInfo)
    
    def __init__(self, url=None, parent=None):
        super(RedirectInfo, self).__init__()
        self._url = None
        self._parent = None
        self._hook_enabled = False
        
        self.url = url
        self.parent = parent

    class parent(classproperty):
        def fget(self):
            return self._parent
        def fset(self, parent): 
            if self.parent != parent: 
                self.parent = parent
                self._p_changed = 1

    class url(classproperty):
        def fget(self):
            return self._url
        def fset(self, url): 
            if self._url != url: 
                self._url = clean_host(url)
                self._p_changed = 1

    class hook_enabled(classproperty):
        def fget(self):

            return self._hook_enabled
        def fset(self, val):
            if self._hook_enabled != val:
                self._hook_enabled = val
                self._p_changed = 1

    def __repr__(self):
        return "%s -> '%s' => %s" %(Persistent.__repr__(self),
                                    self.url,
                                    super(RedirectInfo, self).__repr__())

# == utility == #

class DefaultRedirectInfo(SimpleItem):
    implements(IDefaultRedirectInfo)
    
    def __init__(self, host='', ignore_path=''):
        self.host = host
        self.ignore_path = ignore_path

    class host(classproperty):
        def fget(self):
            return self._host
        def fset(self, val):
            self._host = clean_host(val)
            self._p_changed = 1

    class ignore_path(classproperty):
        def fget(self):
            return self._ignore_path
        def fset(self, val):
            self._ignore_path = val
            self._p_changed = 1

    def default_url_for(self, obj):
        if not self.host:
            return ''

        path = '/'.join(obj.getPhysicalPath())

        if self.ignore_path and path.startswith(self.ignore_path):
            path = path[len(self.ignore_path):]
            if not path.startswith('/'):
                path = '/%s' % path

        assert('://' in self.host)
        url = urlparse.urljoin(self.host, path)

        logger.info("Default URL for %s is %s" % (obj, url))
        return url

# == subscribers == #

def redispatch(event):
    handle(event.obj, event)

@adapter(IRedirectEvent)
def log_redirect_event(event):
    logger.info("%s -- %s" %(event.request.getURL(), event.obj))

@adapter(IRedirectManagementEvent)
def log_redirect_management_event(event):
    logger.info("%s -- %s" %(event, event.obj))


@adapter(IRedirected, IRedirectEvent)
def trigger_redirection(obj, event):
    logger.debug("Checking redirection on %s" %  obj)

    request=event.request
    if should_ignore(obj, request):
        return 
        
    server_url = request.get('SERVER_URL')
    
    base_url = get_annotation(obj,REDIRECT_ANNOTATION).url

    if not base_url:
        # no specific url, try default
        default_info = queryUtility(IDefaultRedirectInfo, 
                                    default=None, context=obj)
        if default_info is not None:
            base_url = default_info.default_url_for(obj)

    if base_url and not hosts_match(server_url, base_url):
        logger.debug("redirecting request "
                     "for %s to %s (%s != %s)" % (request['ACTUAL_URL'],
                                                  base_url, 
                                                  extract_host(server_url),
                                                  extract_host(base_url)))
        do_relative_redirect(request, base_url)

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

    logger.info("Redirecting to %s" % url)
    raise Redirect, url


# == hook functions == #

class RedirectHook(AccessEventHook):
    event = RedirectEvent


def enableRedirectHook(obj):
    cfg = get_info(obj)
    if not cfg.hook_enabled: 
        logger.info("Enabling redirect hook on %s" % obj)
        enableAccessEventHook(obj, hook_class=RedirectHook, hook_name=HOOK_NAME)
        cfg.hook_enabled = True
    else:
        logger.debug("Redirect hook is already enabled for %s" % obj)

def disableRedirectHook(obj):
    cfg = get_info(obj)
    if cfg.hook_enabled: 
        logger.info("Disabling redirect hook on %s" % obj)
        disableAccessEventHook(obj, HOOK_NAME)
        cfg.hook_enabled = False
    else:
        logger.debug("Redirect hook is not enabled for %s" % obj)
    

# == convenience functions == #

def activate(obj, url=None):
    
    alsoProvides(obj, IRedirected)
    url = clean_host(url)

    logger.info("Activating redirection on %s, url=%s" %
                (obj, url))
    
    info = get_annotation(obj, REDIRECT_ANNOTATION, factory=RedirectInfo, url=url)

    info.url = url
    enableRedirectHook(obj)

    event.notify(RedirectActivationEvent(obj))
    return info

apply_redirect = activate


def get_redirect_url(obj):
    try:
        return getattr(get_redirect_info(obj), 'url', None)
    except TypeError:
        return None


def deactivate(obj):
    logger.info("Deactivating redirection on %s" %
                obj)
    noLongerProvides(obj, IRedirected)
    disableRedirectHook(obj)
    event.notify(RedirectDeactivationEvent(obj))


def get_info(obj):
    return get_annotation(obj, REDIRECT_ANNOTATION)

    
# == helpers == #

def get_annotation(obj, key, **kwargs):
    ann = IAnnotations(obj)
    notes = ann.get(key)
    if notes is None and kwargs:
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
    if (not IRedirected.providedBy(ob) or
        not publishing or
        RESERVED_PREFIX in request['PATH_INFO'] or 
        RESERVED_PREFIX in request.getURL()):
        return True
    
    return False

def extract_host(url):
    h = urlparse.urlparse(url)[1]
    if ':' in h:
        return h.split(':')[0]
    else:
        return h

def hosts_match(url1, url2):
    return extract_host(url1) == extract_host(url2)

