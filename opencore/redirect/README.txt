OpenCoreRedirect Package Readme
=========================

Overview
--------

see spec for unit explanation of what each piece does. this doctest
will be a functional full z3 registeration demonstration of
how this works.

Main Components
===============

We have utility that stores keys to redirect upon::

    >>> getUtility(IRedirectionMap)
    <IRedirectionMap ...>

We have a function to prune the path to create a key::

    >>> path_slice = slicePath(self.app, self.folder)
    >>> print path_slice
    
We have a traversal adapter to ITraverser

    >>> alsoProvides(self.app, IRedirectableTraversal)
    >>> ITraverser(self.app)
    <SelectiveRedirectTraverser ...>

We have a view that triggers a redirection and consumes the rest of
the subpath.

    >>> getMultiAdapter((self.app,), name='redirect')
    <BrowserView ...>



