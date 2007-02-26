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
    <opencore.redirect.RedirectInfo object at ...>
    
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

    >>> klass = self.app.__bobo_traverse__(request, 'monkey-time').__class__
    >>> klass.debug = True
    >>> import opencore.redirect as mod
    >>> mod.SelectiveRedirectTraverser.debug=True

    >>> print http(r'''
    ... GET /monkey-time/and/more HTTP/1.1
    ... ''')
    HTTP/1.1 302 Moved Temporarily
    Content-Length: 0
    Location: http://redirected/monkey-time/and/more...


Internal Subpath Redirection
============================

The selective redirect traverser also allows for the return of certain
subobject as if they were members of the current container. These
redirects only occur if we are inside the correct url, so we will need
to set our redirect url to match our current test url::

    >>> import transaction as txn
    >>> info = apply_redirect(self.app, url="http://localhost", parent=None)

Next, we'll want to set self.folder as our redirect target(the path
segment is the key for now)::

    >>> st(); info[self.folder.getId()] = '/'.join(self.folder.getPhysicalPath())

    @@ add another folder so we get some actually redirect
