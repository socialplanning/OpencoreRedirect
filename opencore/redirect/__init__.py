from BTrees.OOBTree import OOBTree
from Products.Five import BrowserView
from Products.Five.traversable import FiveTraversable
from interfaces import IRedirectMapping    
from memojito import memoizedproperty
from opencore.redirect.site import get_redirectstore
from opencore.redirect.interfaces import IRedirectable
from persistent.list import PersistentList
from topp.viewtraverser.traverser import ViewTraverser, Traverser
from zope.component import getMultiAdapter
from zope.interface import implements

try:
    from zope.annotation.interfaces import IAnnotations
except ImportError:
    from zope.app.annotation.interfaces import IAnnotations

import logging


_marker = object()
LOG=PATH_KEY = "opencore.redirect"


class RedirectStore(OOBTree):
    implements(IRedirectMapping)

    def __init__(self, id_):
        super(RedirectStore, self).__init__()
        self.id = id_


def get_search_paths(store):
    ann = IAnnotations(store)
    paths = ann.get(PATH_KEY)
    if not paths:
        ann[PATH_KEY] = PersistentList()
        paths = ann[PATH_KEY]
    return paths


class SelectiveRedirectTraverser(ViewTraverser):
    """if a path matches a criterion, check agains mapping, and redirect if necessary"""
    adapts(IRedirectable)

    viewname = "opencore.redirector"

    @memoizedproperty
    def store(self):
        return get_redirectstore()

    @property    
    def redirect_url(self):
        return self.store.get(path, None)
    
    def traverse(self, path, default=_marker, request=None):
        if self.redirect_url:
            obj = ViewTraverser.traverse(self, path, default=_marker, request=request)
            obj.redirect_url = self.redirect_url
            obj.store = self.store
            return obj
        
        return Traverser.traverse(self, path, default=_marker, request=request)


class Redirector(BrowserView, FiveTraversable):
    redirect_url = None
    store = None
    subpath = []
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def redirect(self):
        url = self.redirect_url, '/'.join(self.subpath)
        self.request.RESPONSE.redirect("%s/%s" %url)
        self.logger.info("Redirected to %s" %url)

    def traverse( self, name, furtherPath ):
        # slurp path
        while furtherPath:
            self.subpath.append( furtherPath.pop( 0 ) )
        return self
    
    @property
    def logger(self):
        return logging.getLogger(LOG)
