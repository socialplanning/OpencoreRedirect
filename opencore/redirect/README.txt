OpenCoreRedirect Package Readme
=========================

    >>> import pdb; st = pdb.set_trace

Overview
--------

see spec for unit explanation of what each piece does. this doctest
will be a functional full z3 registeration demonstration of
how this works.


Main Components
===============

We have function that setups a redirection::

    >>> from opencore.redirect import apply_redirect
    >>> apply_redirect(self.app, url="http://redirected", parent=None)
    <opencore.redirect.RedirectInfo object at ...> -> 'http://redirected' => {}
    
We have a traversal adapter to ITraverser

    >>> alsoProvides(self.app, IRedirected)
    >>> ITraverser(self.app)
    <opencore.redirect.SelectiveRedirectTraverser object at ...>

We have a view on our annotation that triggers a redirection and
consumes the rest of the subpath.

    >>> request = self.new_request
    >>> info = get_redirect_info(self.app)
    >>> getMultiAdapter((info, request), name='opencore.redirect')
    <Products.Five.metaclass.Redirector object at ...>


The annotation
==============

The info object is a BTree for storing subpath info(read, aliases) and has 2
attributes storing the redirect info for the context itself: url and parent.

    >>> info.url
    'http://redirected'

Parent is unset and for meant for use with a subpath object::

    >>> info.parent
    
We can add the default folder as a subpath like so::

    >>> info['sub-project'] = '/'.join(self.folder.getPhysicalPath())
    
We use the physical path because later, we'll use this path to
retrieve the subpath object.

Note the change in representation for the info object::

    >>> print info
    <...> -> 'http://redirected' => {'sub-project': '/test_folder_1_'}

The view
========

The view harvests the subpath as zope2.9 pushes the view through the
rest of traversal. Note: this will change in 2.10 to use the z3
signature of (name, furtherPath).  method (returns itself for
publishing).  When the end of traversal is reached, the redirect
method is called(we'll test the property used to seed the redirect
here)::

    >>> redirector = getMultiAdapter((info, request), name='opencore.redirect')
    >>> redirector.path_start = 'sub-project'
    >>> redirector.traverse(['further'], request=request)
    <Products.Five.metaclass.Redirector object at ...>

    >>> redirector.traverse(['path'], request=request)
    <Products.Five.metaclass.Redirector object at ...>

    >>> redirector.url
    'http://redirected/sub-project/further/path'

This sets us up to do the redirect which will occur when the publisher
calls the 'redirect' method (the attribute registered for publish this
view)::

    >>> response = redirector.redirect();
    >>> response.status
    302

    >>> response.headers['location']
    'http://redirected/sub-project/further/path'


The Traverser
=============

Traversing past self.app now will redirect by returning the redirector::

    >>> self.app.__bobo_traverse__(request, 'monkey-time')
    <Products.Five.metaclass.Redirector object at ...>

    >>> print http(r'''
    ... GET /monkey-time HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily
    Content-Length: 0
    Location: http://redirected/monkey-time...


    >>> print http(r'''
    ... GET /monkey-time/and/more HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily
    Content-Length: 0
    Location: http://redirected/monkey-time/and/more...


Internal Subpath Redirection
============================

Selective traversal does one more trick; it looks up and returns
aliases stored in the annotation's btree. This only occurs if the
traverser sees that the request is from the redirected url::

    >>> request._environ['SERVER_URL'] = 'http://redirected'

we'll need another folder to redirect into(basically we will hop over
self.folder when we do this redirect and act as if our new
folder is a root folder)::

    >>> subproject = add_folder(self.folder, 'my-subproject')

@@ test case hack to make sure index.html is available::

    >>> alsoProvides(subproject, ITestObject)

Then we need to inform our annotation of the redirection::

    >>> info[subproject.getId()] = '/'.join(subproject.getPhysicalPath())

This could be arbitrary as long as the key is unique::

    >>> info['disney-land'] = '/'.join(subproject.getPhysicalPath())


A traversal should return our subproject::

    >>> self.app.__bobo_traverse__(request, 'my-subproject')
    <Folder at /test_folder_1_/my-subproject>

    >>> self.app.__bobo_traverse__(request, 'disney-land')
    <Folder at /test_folder_1_/my-subproject>

Let's go through the publisher in proper now::

    >>> info.url="http://localhost"
    >>> info['candy-mountain'] = '/'.join(subproject.getPhysicalPath())
    >>> print http(r'''
    ... GET /candy-mountain/index.html HTTP/1.1
    ... ''')
    HTTP/1.1 200 OK
    Content-Length: 117
    Content-Type: text/html; charset=iso-8859-15...
    Actual   URL: http://localhost/candy-mountain/index.html
    Physical URL: http://localhost/test_folder_1_/my-subproject...

Traversal compliance
====================

We also need to make sure we can get traverse normally to existing
objects within our container::

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


Finally, when we remove the marker, we want traversal to return to normal::

    
