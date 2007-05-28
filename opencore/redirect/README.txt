OpenCoreRedirect Package Readme
===============================


Overview
--------

this doctest will be a functional full z3 registeration demonstration
of how this works.


Main Components
===============

We have function that setups a redirection::

    >>> from opencore import redirect
    >>> from opencore.redirect import get_redirect_info
    >>> redirect.activate(self.app, url="http://redirected")
    <opencore.redirect.RedirectInfo object at ...> -> 'http://redirected' => {}

    >>> self.app.__before_traverse__
    {...(1, '__redirection_hook__'): <...AccessRule instance at ...>...}

A redirection management event should be fired and logged::

    >>> print self.log
    opencore.redirect ...INFO
      <...RedirectActivationEvent object at ...> -- <Application at >...


The annotation
==============

We can retrieve the configuration that was setup 

    >>> info = get_redirect_info(self.app)
    >>> info.url
    'http://redirected'


Traversal Hooks
===============

We'll try to retrieve test_folder_1_, so we mark it with
ITestObject to provide a default view)::

    >>> alsoProvides(self.folder, ITestObject)

Traversing past self.app now will redirect to the url
specified 

   
    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://redirected/test_folder_1_...

The redirector determines when to redirect based on
the Host header.  If we request the object at the
proper URL, there is no redirection.

    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... Host: redirected
    ... ''')
    HTTP/1.1 200 OK...
 
Let's try an extended path::

    >>> print http(r'''
    ... GET /monkey-time/and/more HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://redirected/monkey-time/and/more...



Default Redirection
==================================================

Default redirection information can be added by providing
a utility of type IDefaultRedirectInfo
    >>> from zope.component import queryUtility
    >>> from five.intid.site import addUtility
    >>> from opencore.redirect import DefaultRedirectInfo
    >>> addUtility(self.app, redirect.IDefaultRedirectInfo, redirect.DefaultRedirectInfo, findroot=False)
    >>> default_info = queryUtility(redirect.IDefaultRedirectInfo, context=self.app, default=None)
    >>> default_info
    <DefaultRedirectInfo at /utilities/>
    >>> default_info.host = 'http://default'

If redirection is activated with no url,
the IDefaultRedirectInfo utility is used to determine
the redirection location. 

    >>> info = redirect.activate(self.app)

    >>> self.app.__before_traverse__
    {...(1, '__redirection_hook__'): <...AccessRule instance at ...>...}

    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://default/test_folder_1_...

Again if the host header is set to the correct host,
no redirection is performed.

    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... Host: default
    ... ''')
    HTTP/1.1 200 OK...
    
If we reactivate with a url, things behave as before:
    >>> info = redirect.activate(self.app, url="http://redirected")
    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://redirected/test_folder_1_...

    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... Host: redirected
    ... ''')
    HTTP/1.1 200 OK...

Deactivation 
=================================================

    >>> redirect.deactivate(self.app)
    >>> self.app.__before_traverse__.has_key((1, '__redirection_hook__'))
    False

A deactivation event should appear in our log::

    >>> print self.log 
    opencore.redirect ...INFO
      <...RedirectDeactivationEvent object at ...> -- <Application at >...

Now no matter what the host header is it should be requestable
as normal 
    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... Host: balloonmonkey
    ... ''')
    HTTP/1.1 200...

Traversal compliance
====================

Activating redirection again,

    >>> info = redirect.activate(self.app, url="http://redirected")

We want to assure that  defaulting redirection occurs when 
the object is acquired through a redirected object::

    >>> defaulting = add_folder(self.app, 'defaulting')
    >>> info = redirect.activate(defaulting)
    >>> print http(r'''
    ... GET /test_folder_1_/defaulting HTTP/1.1
    ... Host: redirected
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://default/defaulting...

Sometimes folders will be nested.  We need to assure all path segments
are preserved. Let's create a scenario::


    >>> redirect.deactivate(defaulting)
    >>> ndf = add_folder(defaulting, 'nested_defaulting')
    >>> nef = add_folder(defaulting, 'nested_explicit')
    >>> d_info = redirect.activate(ndf)
    >>> e_info = redirect.activate(nef, url='http://redirected/')

We'll wire the fake request to simulate changes in the vhosting
First we need to make sure that the redirect in is
calculated correctly::

    >>> from opencore.redirect.interfaces import IDefaultRedirectInfo
    >>> dhi = queryUtility(IDefaultRedirectInfo,
    ...                    default=None, context=self.app)
    >>> dhi is not None
    True
    >>> dhi.default_url_for(ndf)
    'http://default/defaulting/nested_defaulting'
    
    >>> dhi.ignore_path = '/defaulting'
    >>> dhi.default_url_for(ndf)
    'http://default/nested_defaulting'
    >>> dhi.ignore_path = ''

This should work if the object is acq wrapped in another::

    >>> dhi.default_url_for(ndf.__of__(nef))
    'http://default/defaulting/nested_defaulting'



    >>> print http(r'''
    ... GET /defaulting/nested_explicit/nested_defaulting HTTP/1.1
    ... Host: redirected
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://default/defaulting/nested_defaulting...

