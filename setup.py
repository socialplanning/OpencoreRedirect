from setuptools import setup, find_packages
import sys, os

version = '0.2'

deplinks = ["https://svn.openplans.org/svn/OpencoreRedirect/branches/whit-bughunt0703/dependency_links.html",
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
          "five.intid==dev,>0.1",
          "plone.app.form",
          "plone.fieldsets"
      ],
      entry_points="",
      dependency_links=deplinks
      )
