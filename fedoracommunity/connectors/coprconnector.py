# This file is part of Fedora Community.
# Copyright (C) 2008-2010  Red Hat, Inc.
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

from fedoracommunity.connectors.api import IConnector, ICall, IQuery
from tg import config
from fedoracommunity.search import utils

import urllib
import requests

try:
    import json
except ImportError:
    import simplejson as json

class CoprConnector(IConnector, ICall, IQuery):
    _method_paths = {}
    _query_paths = {}
    _cache_prompts = {}

    def __init__(self, environ=None, request=None):
        super(CoprConnector, self).__init__(environ, request)

    # IConnector
    @classmethod
    def register(cls):
        cls.register_search_copr_packages()

    @classmethod
    def register_search_copr_packages(cls):
        path = cls.register_query(
                      'search_copr_packages',
                      cls.search_copr_packages,
                      cache_prompt=None,
                      primary_key_col='name',
                      default_sort_col='name',
                      default_sort_order=-1,
                      can_paginate=True)

        path.register_column('name',
                             default_visible=True,
                             can_sort=False,
                             can_filter_wildcards=False)

        path.register_column('summary',
                             default_visible=True,
                             can_sort=False,
                             can_filter_wildcards=False)

    def search_copr_packages(self, start_row=None,
                        rows_per_page=None,
                        order=-1,
                        sort_col=None,
                        filters={},
                        **params):

        url = "https://copr.fedorainfracloud.org/api_3/project/search?query={0}".format(search_string)
        headers = {'Accept': 'application/json'}

        response = requests.get(url, headers=headers)
        if response.status_code == requests.codes['ok']:
            results = response.json()['items']
        else: return (0, [])

        projects = []
        for result in results:
            project = {
                "name" : result["full_name"],
                "description" : result["description"],
            }

            if project["name"][0] == "@":
                project["link"] = "https://copr.fedorainfracloud.org/coprs/g/{0}/".format(
                    project["name"][1:]
                )
            else:
                project["link"] = "https://copr.fedorainfracloud.org/coprs/{0}/".format(
                    project["name"]
                )

            projects.append(project)

        return (len(projects), projects)
