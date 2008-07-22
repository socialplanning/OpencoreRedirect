from setuptools import setup, find_packages
import sys, os

version = '0.4.1'

deplinks = ['http://svn.openplans.org/eggs/',
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
          "five.intid==0.2.0",
          "plone.app.form==0.1dev_r15470", 
          "plone.fieldsets==1.0", # higher than this requires plone3/zope2.10
          "collective.testing==0.3"
      ],
      entry_points="",
      dependency_links=deplinks
      )
