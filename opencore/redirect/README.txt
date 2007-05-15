OpenCoreRedirect Package Readme
===============================

    >>> import pdb; st = pdb.set_trace

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

Traversing past self.app now will redirect to the url
specified 

    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://redirected/test_folder_1_...

Let's try an extended path::

    >>> print http(r'''
    ... GET /monkey-time/and/more HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://redirected/monkey-time/and/more...



Deactivation 
=================================================

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

Default Redirection
==================================================

If redirection is activated 

    >>> info = redirect.activate(self.app, explicit=False)
    >>> redirect.IRedirected.providedBy(self.app)
    False
    
    >>> self.app.__before_traverse__
    {...(1, '__redirection_hook__'): <...AccessRule instance at ...>...}

As usual, the hook fires the redirect event with the request and
container as arguments.  A listener handles all these dispatches,
filtering IRedirected and applying defaulting redirecting to the
request. We'll simulate by hand::

    >>> request._post_traverse=True
    >>> event = redirect.RedirectEvent(self.app, request)
    >>> redirect.defaulting_redirection(self.app, event)

The response will reflect the redirection(along with the state we've
applied to the request object in previous tests)::

    >>> request.RESPONSE.headers.get('location')
    'http://localhost:8080'

    >>> request.RESPONSE.status
    302

If we reactivate, the listener will bail out(indicated by False)::

    >>> info = redirect.activate(self.app, url="http://redirected", parent=None)
    >>> redirect.defaulting_redirection(self.app, event)
    False

    
Traversal compliance
====================

We also need to make sure we can traverse normally to existing
objects within our container. (we mark our folders with ITestObject to
provide a default view)::

    >>> alsoProvides(self.folder, ITestObject)
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



