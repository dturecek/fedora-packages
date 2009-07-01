# This file is part of Fedora Community.
# Copyright (C) 2008-2009  Red Hat, Inc.
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

from pylons import cache
from fedora.client import Wiki
from datetime import datetime, timedelta
from moksha.api.widgets import Grid
from moksha.api.widgets.containers import DashboardContainer
from moksha.lib.helpers import Category, Widget as MokshaWidget, defaultdict
from moksha.api.connectors import get_connector
from fedoracommunity.widgets.flot import FlotWidget

def get_wiki_statistics(days=7, show=10):
    """ Get some wiki statistics in multiple formats """
    stats = {
        # most_active_pages is a Grid
        'most_active_pages': [],
        # most_active_users is a FlotWidget
        'most_active_users': {'data': [], 'options': {'xaxis': {}}},
    }

    users = defaultdict(list) # {username: [change,]}
    pages = defaultdict(int)  # {pagename: # of edits}
    pages_last_edited_by = {} # {pagename: username}

    # FIXME: I don't think the Wiki object pays attention to `now`...
    now = datetime.utcnow()
    then = now - timedelta(days=days)

    wiki = Wiki()
    changes = wiki.get_recent_changes(now=now, then=then)

    for change in changes:
        users[change['user']].append(change['title'])
        pages[change['title']] += 1
        if change['title'] not in pages_last_edited_by.keys():
            pages_last_edited_by[change['title']] = change['user']

    ## Determine the most active wiki pages
    most_active_pages = sorted(pages.items(),
            cmp=lambda x, y : cmp(x[1], y[1]),
            reverse=True)[:show]

    page_data = []
    for i, page in enumerate(most_active_pages):
        page_data.append({'title': page, 'last_edited_by':
                          pages_last_edited_by[page[0]]})

    stats['most_active_pages'] = page_data

    ## Determine the most active wiki users
    most_active_users = sorted(users.items(),
            cmp=lambda x, y: cmp(len(x[1]), len(y[1])),
            reverse=True)[:show]

    user_data = []
    user_ticks = []
    for i, user in enumerate(most_active_users):
        user_data.append([i, len(user[1])])
        user_ticks.append([i + 0.5, user[0]])

    stats['most_active_users']['options']['xaxis']['ticks'] = user_ticks
    stats['most_active_users']['data'].append({'data': []}) # color hack
    stats['most_active_users']['data'].append({
        'data': user_data,
        'bars': {'show': True}
        })

    return stats


class MostActiveWikiPages(Grid):
    template = 'mako:fedoracommunity.mokshaapps.statistics.templates.wiki_active_pages'
    resource = 'wiki'
    resource_path='query_most_active_pages'


most_active_wiki_pages = MostActiveWikiPages('most_active_wiki_pages')


class MostActiveWikiUsers(FlotWidget):
    days = 7
    show = 5

    def update_params(self, d):
        wiki_cache = cache.get_cache('wiki')
        stats = wiki_cache.get_value(key='most_active_wiki_users',
                createfunc=get_wiki_statistics,
                expiretime=3600)
        d.data = stats['most_active_users']['data']
        d.options = stats['most_active_users']['options']
        super(MostActiveWikiUsers, self).update_params(d)


most_active_wiki_users = MostActiveWikiUsers('most_active_wiki_users')


class WikiStatisticsDashboard(DashboardContainer):
    layout = [
            Category('left-content-column-apps', [
                MokshaWidget('Most Active Wiki Pages', most_active_wiki_pages),
                MokshaWidget('Most Active Wiki Users', most_active_wiki_users),
                ]),
    ]

wiki_stats_dashboard = WikiStatisticsDashboard('wiki_stats')
