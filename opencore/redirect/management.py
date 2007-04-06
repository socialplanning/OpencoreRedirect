from zope.interface import Interface, implements
from zope.component import adapts
from zope.formlib import form
from plone.app.form.validators import null_validator
from interfaces import IRedirectSetup
from opencore import redirect 
from opencore.redirect import LOG
import logging
from memojito import memoizedproperty

from opencore.redirect.classproperty import property as classproperty
from opencore import redirect 
from plone.fieldsets.form import FieldsetsEditForm
from OFS.Folder import Folder

class RedirectConfigSchemaAdapter(object):
    adapts(Folder)
    implements(IRedirectSetup)
    
    def __init__(self, context):
        self.context = context
##         ptool = getUtility(IPropertiesTool)
##         self.encoding = ptool.getProperty('default_charset', None)

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



class RedirectSetupForm(FieldsetsEditForm): 
    form_fields = form.FormFields(IRedirectSetup)

    label = 'Activate Redirection' 

    @form.action('Save changes')
    def handle_edit_action(self, action, data):
        if form.applyChanges(self.context, self.form_fields, data,
                             self.adapters):
            self.status = "Redirection changes saved."
        else:
            self.status = "No changes made."

    @form.action(u'Cancel', validator=null_validator)
    def handle_cancel_action(self, action, data):
        IStatusMessage(self.request).addStatusMessage("Changes canceled.", type="info")
        url = getMultiAdapter((self.context, self.request), name='absolute_url')()
        self.request.response.redirect(url)
        return

##     @form.action('Activate')
##     def handle_activate_action(self, action, data): 
##         redirect_url = data.get('redirect_url')
        
##         logging.getLogger(LOG).info("Setting redirect url %s on %s" % (redirect_url, self.context))
##         redirect.activate(self.context, url=redirect_url)
##         self.status = "Activated Redirection"
