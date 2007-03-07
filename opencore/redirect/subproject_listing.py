from Products.OpenPlans.browser.projectlisting import ProjectListingView 
from memojito import memoizedproperty

from opencore.redirect import get_redirect_info
from Products.CMFCore.utils import getToolByName

class SubProjectListingView(ProjectListingView): 
    """
    """

    @memoizedproperty
    def redirect_info(self): 
        return get_redirect_info(self.context)

    @property
    def project_paths(self):
        return list(self.redirect_info.values())

    @memoizedproperty
    def portal_catalog(self):
        return getToolByName(self, 'portal_catalog')
        
    @memoizedproperty
    def allprojects(self): 
        return self.portal_catalog(path=self.project_paths, sort_on='sortable_title')

    @property
    def alpha(self): 
        """ 
        this is just to eh assert that this view is 
        being called, just delete this at some point. 
        """ 
        for letter in "balloon": 
            yield letter 

