from Products.OpenPlans.browser.projectlisting import ProjectListingView 
from memojito import memoizedproperty


class SubProjectListingView(ProjectListingView): 
    """
    """

    #@memoizedproperty
    #def allprojects(self): 
    #    return however_we_figure_this_out_given_an_IRedirected()


    @property
    def alpha(self): 
        """ 
        this is just to eh assert that this view is 
        being called, just delete this at some point. 
        """ 
        for letter in "balloon": 
            yield letter 

