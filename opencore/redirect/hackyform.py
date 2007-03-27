"""
a crap zmi view for activating and editing redirection 
"""

from zope.interface import Interface
from zope.formlib import form 
from Products.Five.formlib import formbase
from zope import schema

from opencore import redirect 
from opencore.redirect import LOG
import logging 


class IRedirectSetup(Interface): 
    
    redirect_url = schema.TextLine(
        title = u'Redirect URL', 
        required = True, 
        description = u'redirect to this url')



class RedirectSetupForm(formbase.PageForm): 
    form_fields = form.FormFields(IRedirectSetup)

    label = 'Activate Redirection' 

    def render(self):
        redirect_url = redirect.get_redirect_url(self.context)
        if redirect_url is None:
            self.label = 'Activate Redirection' 
        else:
            self.label = 'Currently Redirecting to: %s' % redirect_url
        return formbase.PageForm.render(self)

    @form.action('Activate')
    def handle_activate_action(self, action, data): 
        redirect_url = data.get('redirect_url')
        
        logging.getLogger(LOG).info("Setting redirect url %s on %s" % (redirect_url, self.context))
        redirect.activate(self.context, url=redirect_url)
        self.status = "Activated Redirection"

    @form.action('Deactivate', validator=lambda *args:())
    def handle_deactivate_action(self, action, data):
        redirect_url = redirect.get_redirect_url(self.context)
        if redirect_url is None:
            self.status = "Error: No Redirection to Deactivate"
        else:
            logging.getLogger(LOG).info("Deactivating redirect url %s on %s" % (redirect_url, self.context))
            redirect.deactivate(self.context)
            self.status = "Deactivated Redirection"
