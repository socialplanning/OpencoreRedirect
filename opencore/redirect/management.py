from OFS.Folder import Folder
from Products.Five import BrowserView
from five.intid.site import addUtility
from interfaces import IRedirectSetup, IDefaultRedirectInfoSetup, IDefaultRedirectInfo
from memojito import memoizedproperty
from opencore import redirect 
from opencore.redirect import LOG
from opencore.redirect.classproperty import property as classproperty
from plone.fieldsets.form import FieldsetsEditForm
from zope.app.component.interfaces import ISite, IPossibleSite
from zope.component import adapts, queryUtility
from zope.component.interfaces import ComponentLookupError
from zope.formlib import form
from zope.interface import Interface, implements
import logging

logger = logging.getLogger(LOG)

class BaseAdapter(object):
    def __init__(self, context):
        self.context = context
##         ptool = getUtility(IPropertiesTool)
##         self.encoding = ptool.getProperty('default_charset', None)

class BaseForm(FieldsetsEditForm): 
    @form.action('Save changes')
    def handle_edit_action(self, action, data):
        if form.applyChanges(self.context, self.form_fields, data,
                             self.adapters):
            self.status = "Changes saved."
        else:
            self.status = "No changes made."

    @form.action(u'Cancel', validator=lambda *a: ())
    def handle_cancel_action(self, action, data):
        IStatusMessage(self.request).addStatusMessage("Changes canceled.", type="info")
        url = getMultiAdapter((self.context, self.request), name='absolute_url')()
        self.request.response.redirect(url)
        return


class RedirectSetupForm(BaseForm):
    form_fields = form.FormFields(IRedirectSetup)
    label = 'Activate Redirection' 


class RedirectConfigSchemaAdapter(BaseAdapter):
    adapts(Folder)
    implements(IRedirectSetup)
    
    class redirect_url(classproperty):
        def fget(self):
            info = redirect.get_info(self.context)
            if info is not None:
                return info.url
            else:
                return ''
            
        def fset(self, val):
            info = redirect.get_info(self.context, create_if_necessary=True)
            info.url = val

    class alias_pattern(classproperty):
        def fget(self):
            info = redirect.get_info(self.context)
            if info is not None:
                return info.alias_pattern
            else:
                return ''
        def fset(self, pat):
            info = redirect.get_info(self.context, create_if_necessary=True)
            info.alias_pattern = pat
            
    class activate(classproperty):
        def fget(self):
            return redirect.IRedirected.providedBy(self.context)

        def fset(self, val):
            if val:
                return redirect.activate(self.context, self.redirect_url)
            return redirect.deactivate(self.context)


class RedirectDestroy(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.has_info = redirect.get_info(context) is not None

        if self.request.get('destroy', None) is not None:
            redirect.deactivate(context)
            redirect._deannotate(context)
            logger.info("destroyed redirection related info for %s" % context)


class DefaultRedirectInfoForm(BaseForm):
    form_fields = form.FormFields(IDefaultRedirectInfoSetup)
    label = 'Configure Default Redirection'

class DefaultRedirectInfoSchemaAdapter(BaseAdapter):
    adapts(IPossibleSite)
    implements(IDefaultRedirectInfoSetup)

    @memoizedproperty
    def redir_info(self):
        ctx = queryUtility(IDefaultRedirectInfo, default=None)
        if ctx is None:
            raise ComponentLookupError("Default redirect has not been installed yet.")
        return ctx
    
    class url(classproperty):
        def fget(self):
            return self.redir_info.url
        def fset(self, val):
            self.redir_info.url = val

    class ignore_path(classproperty):
        def fget(self):
            return self.redir_info.ignore_path
        def fset(self, val):
            self.redir_info.ignore_path = val

    class alias_pattern(classproperty):
        def fget(self):
            return self.redir_info.alias_pattern
        def fset(self, pat):
            self.redir_info.alias_pattern = pat


class DefaultRedirectInfoInstall(BrowserView):

    def __init__(self, context, request):

        self.context = context
        self.request = request

        doinstall = self.request.get('install', None) and not self.installed
        if doinstall:
            self.install()

    def install(self):
        addUtility(self.context, IDefaultRedirectInfo, redirect.DefaultRedirectInfo, findroot=False)
        logger.info("Persistent default host information installed.")

    @property
    def installed(self):
        return queryUtility(IDefaultRedirectInfo,
                            default=None) is not None

