OpenCoreRedirect Package Readme
=========================

Overview
--------



Explicit Redirection
====================


Explicit redirection allows specification of a
canonical url for an object.  When the object
is reached under a domain which differs
from the canonical url's domain a redirection
to the canonical url is performed, preserving
the remainder of the path beyond the object.


Setting up Explicit Redirection
-------------------------------

visit <yourobject>/opencore_redirect_config

active
~~~~~~
This should be checked if either explicit
redirection or default redirection is desired.
If this is unchecked, opencore redirect
will not do anything with the object. 

Redirect URL
~~~~~~~~~~~~
example: http://someproj.openplans.org

This is the canonical url of the object

Alias Pattern
~~~~~~~~~~~~~
example: (^localhost$)|(^wwwroot.openplans.org$)

A pattern which identifies a set of other acceptable
hostnames which will not be redirected to the
canonical url.  This alias patter overrides the
default alias pattern if specified. If nothing
is specified, the default alias pattern is
used. 

Removing Redirection
--------------------

visit <yourobject>/opencore_redirect_config
and uncheck active.

This will disable the rediction hook for the
object.

To completely remove configuration information
associated with an object, visit:

<yourobject>/opencore_redirect_destroy
click 'Destroy Redirect Info' 



Default Redirection
===================

Default redirection allows specification of a
canonical url which is redirected to when objects
which do not have an explicit url specified
are reached using other urls.

This redirection only applies to objects which have
redirection active. 

For openplans.org this prevents normal projects
from being viewed under the wrong domain or
with an incorrect theme. 


Setting up Default Redirection 
------------------------------
visit <yourportal>/opencore_redirect_install_default
click Install Default Redirect Store

this will create a utility in <yourportal>/utilities
which implements IDefaultRedirectInfo


Configuring Default Redirection
----------------------------------
visit <yourportal>/opencore_redirect_config_default

Default Redirect URL
~~~~~~~~~~~~~~~~~~~~
example: http://www.openplans.org

The canonical base url to redirect objects to


Ignore Path
~~~~~~~~~~~
example: /openplans

Portion of canonical path to an object which this
host masks, eg www.openplans.org masks the
portal name. 

Alias Pattern
~~~~~~~~~~~~~
example: (^localhost$)|(^wwwroot.openplans.org$)

A pattern which identifies a set of other acceptable
hostnames which will not be redirected to the
canonical default url. 


Removing Default Redirection
----------------------------
visit <yourportal>/utilities
remote the IDefaultRedirectInfo utility
