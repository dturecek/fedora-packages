# -*- coding: utf-8 -*-
# This file is part of Fedora Community.
# Copyright (C) 2008-2013  Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import __main__; __main__.__requires__ = __requires__ = ['WebOb>=1.0']; import pkg_resources

import os
import glob

# These two imports are not actually used, but are required to stop tests from
# failing on python 2.7.
import multiprocessing
import logging

from setuptools import setup, find_packages

data_files = [
    ('fedoracommunity/public', filter(os.path.isfile, glob.glob('fedoracommunity/public/*'))),
    ('fedoracommunity/public/css', filter(os.path.isfile, glob.glob('fedoracommunity/public/css/*.css'))),
    ('fedoracommunity/public/css/fonts', filter(os.path.isfile, glob.glob('fedoracommunity/public/css/fonts/*.ttf'))),
    ('fedoracommunity/public/css/filetreetheme', filter(os.path.isfile, glob.glob('fedoracommunity/public/css/filetreetheme/*'))),
    ('fedoracommunity/public/images', filter(os.path.isfile, glob.glob('fedoracommunity/public/images/*'))),
    ('fedoracommunity/public/images/banners', filter(os.path.isfile, glob.glob('fedoracommunity/public/images/banners/*'))),
    ('fedoracommunity/public/images/planet-bubbles', filter(os.path.isfile, glob.glob('fedoracommunity/public/images/planet-bubbles/*'))),
    ('fedoracommunity/public/images/icons', filter(os.path.isfile, glob.glob('fedoracommunity/public/images/icons/*'))),
    ('fedoracommunity/public/images/tour', filter(os.path.isfile, glob.glob('fedoracommunity/public/images/tour/*'))),
    ('fedoracommunity/public/images/tour/screenshots', filter(os.path.isfile, glob.glob('fedoracommunity/public/images/tour/screenshots/*'))),
    ('fedoracommunity/public/misc', filter(os.path.isfile, glob.glob('fedoracommunity/public/misc/*'))),
    ('fedoracommunity/public/javascript', filter(os.path.isfile, glob.glob('fedoracommunity/public/javascript/*.js'))),
]

packages = find_packages()

setup(
    name='fedoracommunity',
    version='4.1.1',
    description='',
    license='AGPLv3',
    authors=('John (J5) Palmieri <johnp@redhat.com>',
             'Luke Macken <lmacken@redhat.com>',
             'Máirín Duffy <duffy@redhat.com>',
             'Ralph Bean <rbean@redhat.com>',
             ),
    url='https://github.com/fedora-infra/fedora-packages',
    install_requires=[
        "moksha.wsgi",
        "TurboGears2",
        "dogpile.cache",
        "python-memcached",
        "markdown",
        "fedmsg",
        #"PyOpenSSL",
        #"SQLAlchemy>=0.5",
        #"xappy",
        # For some reason this doesn't get automatically pulled in :(
        #"GitPython",
        #"pytz",
        ],
    scripts=['bin/fcomm-index-packages'],
    packages=packages,
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['webtest'],
    data_files=data_files,
    package_data={'fedoracommunity': ['i18n/*/LC_MESSAGES/*.mo']},

    entry_points="""
    [setuptools.file_finders]
    git = fedoracommunity.lib.utils:find_git_files

    [paste.app_factory]
    main = fedoracommunity.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller

    # list all the widgets we need for deployment - this is messy but the
    # easiest way to get things working
    [tw2.widgets]
    widgets = fedoracommunity.widgets
    moksha_js = moksha.wsgi.widgets.moksha_js
    fcomm_js = fedoracommunity.connectors.widgets.widgets
    moksha_widgets = moksha.wsgi.widgets.api
    bodhi_js = fedoracommunity.widgets.package.updates:bodhi_js

    fedoracommunity_bodhi_js = fedoracommunity.widgets.package.updates:bodhi_js
    fedoracommunity_updates = fedoracommunity.widgets.package.updates:Updates

    packages = fedoracommunity.widgets.package

    package_overview = fedoracommunity.widgets.package.overview
    package_updates = fedoracommunity.widgets.package.updates
    package_builds = fedoracommunity.widgets.package.builds

    package_bugs = fedoracommunity.widgets.package.bugs
    package_contents = fedoracommunity.widgets.package.contents
    package_changelog = fedoracommunity.widgets.package.changelog
    package_sources = fedoracommunity.widgets.package.sources

    [fcomm.connector]
    koji = fedoracommunity.connectors:KojiConnector
    bodhi = fedoracommunity.connectors:BodhiConnector
    bugzilla = fedoracommunity.connectors:BugzillaConnector
    yum = fedoracommunity.connectors:YumConnector
    xapian = fedoracommunity.connectors:XapianConnector

    [moksha.widget]
    fedoracommunity.bodhi = fedoracommunity.widgets.package.updates:Updates
    grid = fedoracommunity.widgets.grid:Grid

    package_overview = fedoracommunity.widgets.package.overview:Details

    package_updates = fedoracommunity.widgets.package.updates:Updates
    package_builds = fedoracommunity.widgets.package.builds:Builds
    package_bugs = fedoracommunity.widgets.package.bugs:BugsWidget
    package_contents = fedoracommunity.widgets.package.contents:ContentsWidget
    package_changelog = fedoracommunity.widgets.package.changelog:ChangelogWidget
    package_sources = fedoracommunity.widgets.package.sources:Sources
    package_sources_spec = fedoracommunity.widgets.package.sources:Spec
    package_sources_patches = fedoracommunity.widgets.package.sources:Patches
    package_sources_patch = fedoracommunity.widgets.package.sources:Patch

    [moksha.consumer]
    cache_invalidator = fedoracommunity.consumers:CacheInvalidator

    """
)
