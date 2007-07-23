OpenCoreRedirect Package Readme
===============================


Overview
--------

this doctest will be a functional full z3 registration demonstration
of how this works.


Main Components
===============

We have function that sets up a redirection::

    >>> from opencore import redirect
    >>> redirect.activate(self.app, url="http://redirected")
    <opencore.redirect.RedirectInfo object at ...> -> 'http://redirected' => {}

This sets up a pre-traversal hook on the object:

    >>> self.app.__before_traverse__
    {...(1, '__redirection_hook__'): <...AccessRule instance at ...>...}

A redirection management event is fired whenever redirection is
setup or changed:

    >>> print self.log
    opencore.redirect ...INFO
      <...RedirectActivationEvent object at ...> -- <Application at >...


The annotation
==============

We can retrieve the configuration that was setup using get_redirect_info 

    >>> from opencore.redirect import get_redirect_info
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

Let's try an extended path::

    >>> print http(r'''
    ... GET /monkey-time/and/more HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://redirected/monkey-time/and/more...

Or a different host: 
    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... Host: moonbase
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://redirected/test_folder_1_...

The redirector determines when to redirect based on
the Host header.  If we request the object with the
proper Host header set, there is no redirection.

    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... Host: redirected
    ... ''')
    HTTP/1.1 200 OK...

A redirected object can have several permissable
aliases that are not the canonical redirect url.
This is accomplished with a regex pattern:

    >>> info.alias_pattern = "^moonbase$"
    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... Host: moonbase
    ... ''')
    HTTP/1.1 200 OK...
    
    >>> info.alias_pattern = ''
    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... Host: moonbase
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://redirected/test_folder_1_...




Default Redirection
==================================================

A global default for redirection can be added by providing
a utility of type IDefaultRedirectInfo. 

    >>> from five.intid.site import addUtility
    >>> from opencore.redirect import DefaultRedirectInfo
    >>> addUtility(self.app, redirect.IDefaultRedirectInfo, redirect.DefaultRedirectInfo, findroot=False)

It can be retrieved using queryUtility

    >>> from zope.component import queryUtility
    >>> default_info = queryUtility(redirect.IDefaultRedirectInfo, context=self.app, default=None)
    >>> default_info
    <DefaultRedirectInfo at /utilities/>

It can be configured similarly to the RedirectInfo::

    >>> default_info.url = 'http://default'

If redirection is activated with no url specified,
the IDefaultRedirectInfo utility is used to determine
the redirection location.

    >>> info = redirect.activate(self.app)

The hook will still be setup:

    >>> self.app.__before_traverse__
    {...(1, '__redirection_hook__'): <...AccessRule instance at ...>...}

By default this will allow us to access things through the
host specified, _or_ localhost.

    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... ''')
    HTTP/1.1 200 OK...

    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... Host: default
    ... ''')
    HTTP/1.1 200 OK...

If we remove the alias_pattern, localhost will also
produce a redirect.

    >>> default_info.alias_pattern = ''


When we visit the test folder, we'll be redirected to
the default host:

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

The default alias pattern will also apply to
explicitly redirected objects if they have
no alias pattern set.

    >>> default_info.alias_pattern = '^localhost$'
    >>> print http(r'''
    ... GET /test_folder_1_ HTTP/1.1
    ... ''')
    HTTP/1.1 200 OK...


Deactivation 
=================================================

To stop redirection on an object, use deactivate.  This
will remove the hook. 

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
the object is acquired through an explicitly redirected object::

    >>> defaulting = add_folder(self.app, 'defaulting')
    >>> info = redirect.activate(defaulting)
    >>> print http(r'''
    ... GET /test_folder_1_/defaulting HTTP/1.1
    ... Host: redirected
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://default/defaulting...

Sometimes folders will be nested.  We need to assure all path segments
are preserved. Let's create a scenario.  First, a parent folder with no
redirection:

    >>> par = add_folder(self.app, 'parent_folder')

Now, two child folders, one with default redirection, one with
explicit redirection.

    >>> ndefault = add_folder(par, 'ndefault')
    >>> d_info = redirect.activate(ndefault)

    >>> nexplicit = add_folder(par, 'nexplicit')
    >>> e_info = redirect.activate(nexplicit, url='http://redirected/')

First we need to make sure that the default redirect url is
calculated correctly::

    >>> default_info.default_url_for(ndefault)
    'http://default/parent_folder/ndefault'

This should work if the object is acq wrapped in another::

    >>> default_info.default_url_for(ndefault.__of__(nexplicit))
    'http://default/parent_folder/ndefault'

If we request the default redirected object at the redirected
host, we should wind up at the default host:

    >>> print http(r'''
    ... GET /parent_folder/nexplicit/ndefault HTTP/1.1
    ... Host: redirected
    ... ''')
    HTTP/1.1 302 Moved Temporarily...
    Location: http://default/parent_folder/ndefault...


The DefaultHostInfo may also be configured with an 'ignore path'.
This is similar to a virtual host root. When redirecting, this
path will be eliminated from the path to the object, eg we
can eliminate 'parent_folder' from the path to ndefault. 

    >>> default_info.ignore_path = '/parent_folder'
    >>> default_info.default_url_for(ndefault)
    'http://default/ndefault'

