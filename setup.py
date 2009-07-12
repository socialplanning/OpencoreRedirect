from setuptools import setup, find_packages
import sys, os

version = '0.5'

deplinks = ["https://svn.plone.org/svn/collective/five.intid/trunk#egg=five.intid-dev",
            "http://svn.plone.org/svn/plone/plone.fieldsets/trunk#egg=plone.fieldsets",
            "http://svn.plone.org/svn/plone/plone.app.form/branches/plone-3.0#egg=plone.app.form",
            ]

setup(name='OpencoreRedirect',
      version=version,
      description="",
      long_description="""\
""",
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='The Open Planning Project',
      author_email='opencore@lists.openplans.org',
      url='http://openplans.org/projects/opencore',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['opencore'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "five.intid>=0.2.0",
          "plone.app.form>=0.1dev-r15470",
          "plone.fieldsets>=1.0",  # Can probably update this now for plone 3
          "collective.testing>=0.3",  # Don't use collective trunk anymore!
      ],
      entry_points="",
      dependency_links=deplinks
      )
