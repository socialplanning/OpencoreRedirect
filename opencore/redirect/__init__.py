from persistent.list import PersistentList
from BTrees.OOBTree import OOBTree
from zope.interface import implements
from interfaces import IRedirectMapping
try:
    from zope.annotation.interfaces import IAnnotations
except ImportError:
    from zope.app.annotation.interfaces import IAnnotations
    
from topp.viewtraverser.traverser import ViewTraverser

_marker = object()

class RedirectStore(OOBTree):
    implements(IRedirectMapping)

    def __init__(self, id_):
        super(RedirectStore, self).__init__()
        self.id = id_

PATH_KEY = "opencore.redirect"

def get_search_paths(store):
    ann = IAnnotations(store)
    paths = ann.get(PATH_KEY)
    if not paths:
        ann[PATH_KEY] = PersistentList()
        paths = ann[PATH_KEY]
    return paths


class SelectiveRedirectTraverser(ViewTraverser):
    """if a path matches a criterion, check agains mapping, and redirect if necessary"""
