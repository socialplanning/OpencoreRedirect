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

    >>> request = self.folder.REQUEST
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

The view harvests the rest of the subpath from zope in the 'traverse'
method (returns itself for publishing), then constructs our new url to
redirect to in the property 'redirect_url'::

    >>> redirector = getMultiAdapter((info, request), name='opencore.redirect')
    >>> redirector.traverse('sub-project', ['sub-project', 'further', 'path'])
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

Traversing past app now will redirect by returning the ::

    >>> self.app.__bobo_traverse__(request, 'monkey-time')
    <Products.Five.metaclass.Redirector object at ...>
