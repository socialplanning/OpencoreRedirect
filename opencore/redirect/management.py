from OFS.Folder import Folder
from interfaces import IRedirectSetup, IDefaultHost
from memojito import memoizedproperty
from opencore import redirect 
from opencore.redirect import LOG
from opencore.redirect.classproperty import property as classproperty
from plone.app.form.validators import null_validator
from plone.fieldsets.form import FieldsetsEditForm
from zope.app.component.interfaces import ISite, IPossibleSite
from zope.component import adapts, getUtility
from zope.formlib import form
from zope.interface import Interface, implements
import logging
from five.intid.site import addUtility
from Products.Five import BrowserView

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

    @form.action(u'Cancel', validator=null_validator)
    def handle_cancel_action(self, action, data):
        IStatusMessage(self.request).addStatusMessage("Changes canceled.", type="info")
        url = getMultiAdapter((self.context, self.request), name='absolute_url')()
        self.request.response.redirect(url)
        return


class RedirectSetupForm(BaseForm):
    form_fields = form.FormFields(IRedirectSetup)
    label = 'Activate Redirection' 


class DefaultHostForm(BaseForm):
    form_fields = form.FormFields(IDefaultHost)
    label = 'Set Default Host' 


class DefaultHostSchemaAdapter(BaseAdapter):
    adapts(IPossibleSite)
    implements(IDefaultHost)

    @memoizedproperty
    def dh(self):
        return getUtility(IDefaultHost)

    class path(classproperty):
        def fget(self):
            return self.dh.path
            
        def fset(self, val):
            self.dh.path = val

    class host(classproperty):
        def fget(self):
            return self.dh.host
            
        def fset(self, val):
            self.dh.host = val


class RedirectConfigSchemaAdapter(BaseAdapter):
    adapts(Folder)
    implements(IRedirectSetup)
    
    @memoizedproperty
    def info(self):
        return redirect.get_info(self.context)

    class redirect_url(classproperty):
        def fget(self):
            return self.info.url
            
        def fset(self, val):
            self.info.url = val
            
    class activate(classproperty):
        def fget(self):
            return redirect.IRedirected.providedBy(self.context)

        def fset(self, val):
            if val:
                return redirect.activate(self.context, self.redirect_url)
            return redirect.deactivate(self.context)

    # dict/object widget? not worth the work right now
    class subprojects(classproperty):
        def fget(self):
            return self.info
        def fset(self, val):
            for key, value in val:
                self.info[key] = value


class DefaultHostInstall(BrowserView):
    @property
    def context(self):
        return self._context[0]
    
    def __init__(self, context, request):
        self._context = context,
        self.request = request
        doinstall = self.request.get('install', None)
        if doinstall:
            self.install()

    def install(self):
        addUtility(self.context, IDefaultHost, redirect.LocalDefaultHost, findroot=False)

    @property
    def installed(self):
        installed = False
        try:
            dh = getUtility(IDefaultHost)
            if dh and dh is not redirect.global_defaulthost:
                installed = True
        except ComponentLookupError, e:
            pass
        return installed




