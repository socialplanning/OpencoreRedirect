import os, sys, unittest
from zope.testing import doctest
from collective.testing.layer import ZCMLLayer

from zope.testing import doctestunit
from zope.testing import doctest
from zope.component import testing
from Testing import ZopeTestCase as ztc

import warnings; warnings.filterwarnings("ignore")

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

## from opencore.redirect.site import add_redirectstore

def basic_setup(tc):
    alsoProvides(tc.app, IAttributeAnnotateable)

def test_suite():
    from zope.component import getMultiAdapter
    from opencore.redirect import RedirectInfo, IRedirectInfo, IRedirected
    from opencore.redirect import SelectiveRedirectTraverser, ITraverser, get_redirect_info
    from zope.interface import alsoProvides 
    readme = ztc.FunctionalDocFileSuite('README.txt',
                                      package='opencore.redirect',
                                      optionflags=optionflags,
                                      globs=locals())
    
    spec = ztc.FunctionalDocFileSuite('spec.txt',
                                      package='opencore.redirect',
                                      optionflags=optionflags,
                                      globs=locals())
    
    store = ztc.FunctionalDocFileSuite('redirect-store.txt',
                                       package='opencore.redirect',
                                       optionflags=optionflags,
                                       globs=locals())
    suites = (readme,
              #spec,
              #store
              )
    for suite in suites:
        suite.layer = ZCMLLayer
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
