import os, sys, unittest
from zope.testing import doctest
from collective.testing.layer import ZCMLLayer
from collective.testing import utils

from zope.testing import doctestunit
from zope.testing import doctest
from zope.component import testing
from Testing import ZopeTestCase as ztc
from Products.Five import zcml

import warnings; warnings.filterwarnings("ignore")

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

def returno(obj, attr):
    def wrap(*args, **kwargs):
        return getattr(obj, attr, None)
    return wrap

class Bag(object):
    def __init__(self, **kw):
        for key, val in kw.items():
            setattr(self, key, val)

_ppfu = Bag(path=['', 'sub-project', 'further', 'path'])
_url = Bag(url='http://localhost')

## from opencore.redirect.site import add_redirectstore
def readme_setup(tc):
    tc.new_request = utils.new_request()
    import opencore.redirect
    zcml.load_config('test.zcml', opencore.redirect)
    tc.new_request.physicalPathFromURL=returno(_ppfu, 'path')
    tc.new_request.getURL=returno(_url, 'url')
    tc.new_request._hacked_path=None

def test_suite():
    from zope.component import getMultiAdapter
    from opencore.redirect import RedirectInfo, IRedirectInfo, IRedirected
    from opencore.redirect import SelectiveRedirectTraverser, ITraverser, get_redirect_info
    from zope.interface import alsoProvides
    from opencore.redirect.interfaces import ITestObject 
    global _url
    global _ppfu

    def set_path(*path):
        _ppfu.path = path

    def add_folder(container, folder_id):
        from OFS.Folder import manage_addFolder
        manage_addFolder(container, folder_id)
        return getattr(container, folder_id)
    
    readme = ztc.FunctionalDocFileSuite('README.txt',
                                        package='opencore.redirect',
                                        optionflags=optionflags,
                                        setUp=readme_setup,
                                        globs=locals())
    
    spec = ztc.FunctionalDocFileSuite('spec.txt',
                                      package='opencore.redirect',
                                      optionflags=optionflags,
                                      globs=locals())
    
##     store = ztc.FunctionalDocFileSuite('redirect-store.txt',
##                                        package='opencore.redirect',
##                                        optionflags=optionflags,
##                                        globs=locals())
    
    suites = (readme,
              #spec,
              #store
              )
    for suite in suites:
        suite.layer = ZCMLLayer
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
