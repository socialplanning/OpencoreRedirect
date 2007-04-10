from Acquisition import aq_parent
from OFS.SimpleItem import SimpleItem
from OFS.interfaces import IApplication
from Products.Five import BrowserView
from Products.Five.site.localsite import enableLocalSiteHook, disableLocalSiteHook
from opencore.redirect import IRedirectMapping, RedirectStore
from zope.component import getUtility
from zope.app.component.hooks import setSite, setHooks
from zope.app.component.interfaces import ISite, IPossibleSite
from zope.component.interfaces import ComponentLookupError
from zope.interface import implements, implementer

class OFSRedirectStore(RedirectStore, SimpleItem):
    """ Fiveish Store """


# convenience functions
def add_redirectstore(site, findroot=False):
    addUtility(site, IRedirectMapping, OFSRedirectStore, findroot=findroot)


def get_redirectstore(context=None):
    return getUtility(IRedirectMapping, context=context)


def del_redirectstore(context=None, findroot=False):
    if findroot:
        context = get_root(context)
    utility = get_redirectstore(context)
    parent = utility.aq_parent
    parent.manage_delObjects([utility.getId()])


class RedirectStoreInstallView(BrowserView):
    """ installer view """

    add_redirectstore=staticmethod(add_redirectstore)
    get_redirectstore=staticmethod(get_redirectstore)   
    
    @property
    def context(self):
        return self._context[0]
    
    def __init__(self, context, request):
        self._context = context,
        self.request = request
        doinstall = self.request.get('install-redirectstore', None)
        if doinstall:
            self.install_redirectstore()

    def install_redirectstore(self):
        self.add_redirectstore(self.context)

    @property
    def installed(self):
        installed = False
        try:
            redirectstore = self.get_redirectstore(self.context)
            if redirectstore:
                installed = True
        except ComponentLookupError, e:
            pass
        return installed
    

def initializeSite(site, sethook=False, **kw):
    enableLocalSiteHook(site)
    if sethook:
         setHooks()
    setSite(site)


def addUtility(site, interface, klass, name='', findroot=True):
    """
    add local utility in zope2
    """
    app = site
    if findroot:
        app = get_root(site)
    else:
        site = get_site(site)
        
    assert app, TypeError("app is None")

    if not ISite.providedBy(app):
        initializeSite(app, sethook=False)
        
    sm = app.getSiteManager()
    if sm.queryUtility(interface,
                       name=name,
                       default=None) is None:

        if name: obj = klass(name)
        else: obj = klass(interface.__name__)
        sm.registerUtility(interface, obj, name=name)  #2.9


def get_root(app):
    # adapted from alecm's 'listen'
    while app is not None and not IApplication.providedBy(app):
            app = aq_parent(app)
    return app


def get_site(site):
    while site is not None and not (ISite.providedBy(site) or IPossibleSite.providedBy(site)):
        site = aq_parent(site)
    return site
    


