# @@ remove now in opencore.content.project
try:
    from Products.OpenPlans.browser.projectlisting import ProjectListingView
except ImportError:
    from opencore.siteui.projectlisting import ProjectListingView
from memojito import memoizedproperty

from opencore import redirect
from Products.CMFCore.utils import getToolByName

class SubProjectListingView(ProjectListingView): 
    """mandatory docstring
    """
    @memoizedproperty
    def redirect_info(self): 
        return redirect.get_info(self.context)

    @property
    def project_paths(self):
        return list(self.redirect_info.values())

    @memoizedproperty
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')
        
    def allprojects(self): 
        return self.portal_catalog(path=self.project_paths, sort_on='sortable_title')

