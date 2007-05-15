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
    >>> redirect.activate(self.app, url="http://redirected")
    <opencore.redirect.RedirectInfo object at ...> -> 'http://redirected' => {}

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
    >>> addUtility(self.app, redirect.IDefaultRedirectInfo, redirect.DefaultRedirectInfo, findroot=False)
    >>> default_info = queryUtility(redirect.IDefaultRedirectInfo, context=self.app, default=None)
    >>> default_info
    <DefaultRedirectInfo at /utilities/>
    >>> default_info.host = 'http://default'

If redirection is activated with the explicit=False flag,
the IDefaultRedirectInfo utility is used to determine
the redirection location. 

    >>> info = redirect.activate(self.app, explicit=False)

    >>> redirect.IRedirected.providedBy(self.app)
    False

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
    >>> info = redirect.activate(self.app, url="http://redirected", parent=None)
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

If we deactivate without setting disable_hook to True,
the hook will remain active and default redirection will
apply (equivalent to activate with explicit=False)

    >>> redirect.deactivate(self.app)
    >>> self.app.__before_traverse__
    {...(1, '__redirection_hook__'): <...AccessRule instance at ...>...}

    >>> print http(r'''
    ... GET /monkey-time/and/more HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://default/monkey-time/and/more...


To completely deactivate redirection, call deactivate with
disable_hook=True. 

    >>> self.log.clear()
    >>> redirect.deactivate(self.app, disable_hook=True)
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
    >>> Host: balloonmonkey
    ... ''')
    HTTP/1.1 200 OK...

    
Traversal compliance
====================

We also need to make sure we can traverse normally to existing
objects within our container.

    >>> print http(r'''
    ... GET /test_folder_1_/index.html HTTP/1.1
    ... ''')
    HTTP/1.1 200 OK
    Content-Length: 103
    Content-Type: text/html; charset=iso-8859-15...
    Actual   URL: http://localhost/test_folder_1_/index.html
    Physical URL: http://localhost/test_folder_1_...


And to the contents of non-subredirected content::

    >>> print http(r'''
    ... GET /test_folder_1_/my-subproject HTTP/1.1
    ... ''')
    HTTP/1.1 200 OK...
    Actual   URL: http://localhost/test_folder_1_/my-subproject/index.html
    Physical URL: http://localhost/test_folder_1_/my-subproject...


We also want to be sure that traversal fails normally::

    >>> print http(r'''
    ... GET /nothinghere HTTP/1.1
    ... ''')
    HTTP/1.1 404 Not Found...

    >>> print http(r'''
    ... GET /candy-mountain/nothinghere HTTP/1.1
    ... ''')
    HTTP/1.1 404 Not Found...

    >>> print http(r'''
    ... GET /candy-mountain/nothinghere HTTP/1.1
    ... ''')
    HTTP/1.1 404 Not Found...

We want to assure that  defaulting redirection handle unusual
traversal cases of redirect properly::

    >>> defaulting = add_folder(self.app, 'defaulting')
    >>> info = redirect.activate(defaulting, explicit=False)
    >>> print http(r'''
    ... GET /test_folder_1_/defaulting HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily
    Content-Length: ...
    Content-Type: text/html; charset=iso-8859-15
    Location: http://localhost:8080/defaulting...
    Actual   URL: http://localhost/test_folder_1_/defaulting/index.html
    Physical URL: http://localhost/defaulting...

Sometimes folders will be nested.  We need to assure all path segments
are preserved. Let's create a scenario::


    >>> redirect.deactivate(defaulting, disable_hook=True)
    >>> ndf = add_folder(defaulting, 'nested_defaulting')
    >>> nef = add_folder(defaulting, 'nested_explicit')
    >>> d_info = redirect.activate(ndf, explicit=False)
    >>> e_info = redirect.activate(nef, explicit=True)

We'll wire the fake request to simulate changes in the vhosting::

    >>> set_path('')

First we need to make sure that the redirect in is
calculated correctly::

    >>> dhost, path = redirect.get_host_info()
    >>> redirect.default_url_for(dhost, ndf, request, default_path=path)
    'http://localhost:8080/defaulting/nested_defaulting'

This should be robust enough to deal with changes in vhosting::

    >>> set_path('', 'defaulting')
    >>> dhost, path = redirect.get_host_info()
    >>> redirect.default_url_for(dhost, ndf, request, default_path=path)
    'http://localhost:8080/nested_defaulting'
    >>> set_path('')

This should work if the object is acq wrapped in another::

    >>> redirect.default_url_for(dhost, ndf.__of__(nef), request, default_path=path)
    'http://localhost:8080/defaulting/nested_defaulting'

#@@ dunno why the object path doubles up on location...

    >>> print http(r'''
    ... GET /defaulting/nested_explicit/nested_defaulting HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily
    Content-Length: ...
    Content-Type: text/html; charset=iso-8859-15
    Location: http://localhost:8080/defaulting/nested_defaulting...
    Actual   URL: http://localhost/defaulting/nested_explicit/nested_defaulting/index.html
    Physical URL: http://localhost/defaulting/nested_defaulting...



