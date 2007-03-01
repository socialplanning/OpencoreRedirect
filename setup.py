from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='OpenCoreRedirect',
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
          "five.intid==dev"
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      dependency_links=["https://svn.plone.org/svn/collective/five.intid/trunk#egg=five.intid-dev"]
      )
