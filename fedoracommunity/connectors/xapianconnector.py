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
import xapian
import requests

try:
    import json
except ImportError:
    import simplejson as json


class XapianConnector(IConnector, ICall, IQuery):
    _method_paths = {}
    _query_paths = {}
    _cache_prompts = {}

    def __init__(self, environ=None, request=None):
        super(XapianConnector, self).__init__(environ, request)
        self._search_db = xapian.Database(
            config.get('fedoracommunity.connector.xapian.package-search.db',
                       'xapian/search'))

    # IConnector
    @classmethod
    def register(cls):
        cls.register_search_packages()

    def introspect(self):
        # FIXME: return introspection data
        return None

    @classmethod
    def register_search_packages(cls):
        path = cls.register_query(
                      'search_packages',
                      cls.search_packages,
                      cache_prompt=None,  # This means "don't cache".
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

    # IQuery
    def query(self, resource_path, params, _cookies, start_row=0,
              rows_per_page=10,
              sort_col=None,
              sort_order=None,
              filters=dict()):

        results = None
        r = {
            "total_rows": 0,
            "no_fedora_rows": 0,
            "no_copr_rows": 0,
            "rows_per_page": 0,
            "start_row": 0,
            "rows": None,
            "fedora_rows": None,
            "copr_rows": None,
        }

        if not sort_col:
            sort_col = self.get_default_sort_col(resource_path)

        if not sort_order:
            sort_order = self.get_default_sort_order(resource_path)

        if not params:
            params = dict()

        query_func = self.query_model(resource_path).get_query()

        (no_fedora_rows, f_rows, no_copr_rows, c_rows) = query_func(
            self, start_row=start_row, rows_per_page=rows_per_page,
            order=sort_order, sort_col=sort_col, filters=filters,
            **params)

        total_rows = no_fedora_rows + no_copr_rows
        r['total_rows'] = total_rows
        r['no_fedora_rows'] = no_fedora_rows
        r['no_copr_rows'] = no_copr_rows
        r['rows_per_page'] = rows_per_page

        if start_row:
            r['start_row'] = start_row

        # there has been an error
        if total_rows == -1:
            r['error'] = f_rows
        else:
            r['visible_rows'] = total_rows
            r['rows'] = f_rows
            r['fedora_rows'] = f_rows
            r['copr_rows'] = c_rows

        results = r

        return results

    def search_packages(self, start_row=None,
                        rows_per_page=None,
                        order=-1,
                        sort_col=None,
                        filters={},
                        **params):
        search_string = filters.get('search')
        search_fedora = filters.get('fedora')
        search_copr = filters.get('copr')

        # short circut for empty search
        if not search_string or (not search_fedora and not search_copr):
            return (0, [])

        rows = []
        if search_fedora:
            search_string = urllib.unquote_plus(search_string)
            search_string = utils.filter_search_string(search_string)
            phrase = '"%s"' % search_string

            # add exact matchs
            search_terms = search_string.split(' ')
            search_terms = [t.strip() for t in search_terms if t.strip()]
            for term in search_terms:
                search_string += " EX__%s__EX" % term

            # add phrase match
            search_string += " OR %s" % phrase

            if len(search_terms) > 1:
                # add near phrase match (phrases that are near each other)
                search_string += " OR (%s)" % ' NEAR '.join(search_terms)

            # Add partial/wildcard matches
            search_string += " OR (%s)" % ' OR '.join([
                "*%s*" % term for term in search_terms])

            matches = self.do_search(search_string,
                                     start_row,
                                     rows_per_page,
                                     order,
                                     sort_col)

            count = matches.get_matches_estimated()
            for m in matches:
                result = json.loads(m.document.get_data())

                if 'link' not in result:
                    result['link'] = result['name']

                for pkg in result['sub_pkgs']:
                    if 'link' not in pkg:
                        pkg['link'] = pkg['name']

                rows.append(result)

        copr_rows = []
        if search_copr:
            url = "https://copr.fedorainfracloud.org/api_3/project/search?query={0}".format(search_string)
            headers = {'Accept': 'application/json'}

            response = requests.get(url, headers=headers)
            if response.status_code == requests.codes['ok']:
                results = response.json()['items']

                projects = []
                for result in results:
                    project = {
                        "name" : result["full_name"],
                        "description" : result["description"],
                        "summary" : result["description"],
                    }

                    if project["name"][0] == "@":
                        project["link"] = "https://copr.fedorainfracloud.org/coprs/g/{0}/".format(
                            project["name"][1:]
                        )
                    else:
                        project["link"] = "https://copr.fedorainfracloud.org/coprs/{0}/".format(
                            project["name"]
                        )

                    copr_rows.append(project)

        return (len(rows), rows, len(copr_rows), copr_rows)

    def get_package_info(self, package_name):
        search_name = utils.filter_search_string(package_name)
        search_string = "%s EX__%s__EX" % (search_name, search_name)

        matches = self.do_search(search_string, 0, 10)
        if len(matches) == 0:
            return None

        # Sometimes (rarely), the first match is not the one we actually want.
        for match in matches:
            result = json.loads(match.document.get_data())
            if result['name'] == package_name:
                return result
            if any([sp['name'] == package_name for sp in result['sub_pkgs']]):
                return result

        return None

    def do_search(self,
                  search_string,
                  start_row=None,
                  rows_per_page=None,
                  order=-1,
                  sort_col=None):
        enquire = xapian.Enquire(self._search_db)
        qp = xapian.QueryParser()
        qp.set_database(self._search_db)
        flags = xapian.QueryParser.FLAG_DEFAULT | \
            xapian.QueryParser.FLAG_PARTIAL | \
            xapian.QueryParser.FLAG_WILDCARD
        query = qp.parse_query(search_string, flags)

        enquire.set_query(query)
        matches = enquire.get_mset(start_row, rows_per_page)

        return matches
