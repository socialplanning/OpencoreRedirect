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

    @form.action('Activate')
    def handle_edit_action(self, action, data): 
        redirect_url = data.get('redirect_url')
        
        logging.getLogger(LOG).info("Setting redirect url %s on %s" % (redirect_url, self.context))
        redirect.activate(self.context, url=redirect_url)
        self.status = "activated redirection"

