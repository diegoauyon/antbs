#!/usr/bin/env python
#  -*- coding: utf-8 -*-
#
#  build.py
#
#  Copyright © 2016  Antergos
#
#  This file is part of The Antergos Build Server, (AntBS).
#
#  AntBS is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  AntBS is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  The following additional terms are in effect as per Section 7 of the license:
#
#  The preservation of all legal notices and author attributions in
#  the material or in the Appropriate Legal Notices displayed
#  by works containing it is required.
#
#  You should have received a copy of the GNU General Public License
#  along with AntBS; If not, see <http://www.gnu.org/licenses/>.

from views import *

build_view = Blueprint('build', __name__)


def get_builds_with_status(page=None, build_status=None, search=None):
    """
    Get paginated list of build objects.

    Args:
        page (int) Page number.
        build_status (str): Only include builds of this status (completed, failed, etc).
        query (str): Filter list to include builds where "search" string is found in pkgname.

    Returns:
         pkglist (list), all_pages (int), rev_pending (list)

    """
    if page is None or build_status is None:
        abort(500)

    builds_list = []
    rev_pending = []
    all_builds = None
    all_pages = 0

    try:
        all_builds = getattr(status, build_status)
    except Exception as err:
        logger.error('GET_BUILD_INFO - %s', err)
        abort(500)

    if not all_builds:
        return [], 1, []

    if search is not None:
        search_all_builds = [x for x in all_builds if
                             x and match_pkgname_with_build_number(x, search)]
        all_builds = search_all_builds

    if all_builds:
        builds, all_pages = get_paginated(all_builds, 10, page)
        for bnum in builds:
            try:
                bld_obj = get_build_object(bnum=bnum)
            except Exception as err:
                logger.error(err)
                continue

            builds_list.append(bld_obj)

        if user.is_authenticated():
            for bld_obj in builds_list:
                if 'pending' == bld_obj.review_status:
                    rev_pending.append(bld_obj)

    return builds_list, int(all_pages), rev_pending


###
##
#   Views Start Here
##
###


@build_view.route('/<build_status>/search/<query>')
@build_view.route('/<build_status>/search/<query>/<int:page>')
@build_view.route('/<build_status>/<int:page>')
@build_view.route('/<build_status>')
def builds_with_status(build_status=None, page=None, query=None):
    if not build_status or build_status not in ['completed', 'failed']:
        abort(404)

    if page is None:
        page = 1

    builds, all_pages, rev_pending = get_builds_with_status(page, build_status, query)
    pagination = Pagination(page, 10, all_pages)

    return try_render_template('builds/listing.html', builds=builds, all_pages=all_pages,
                               pagination=pagination, build_status=build_status)


@build_view.route('/queue')
def build_queue():
    return try_render_template("builds/scheduled.html", queued=get_build_queue())


@build_view.route('/<int:bnum>')
def build_info(bnum=None):
    if not bnum:
        abort(404)

    bld_obj = None

    try:
        bld_obj = get_build_object(bnum=bnum)
    except Exception:
        abort(500)

    if not bld_obj.log_str:
        bld_obj.log_str = 'Unavailable'

    if bld_obj.container:
        container = bld_obj.container[:20]
    else:
        container = None

    result = 'completed' if bld_obj.completed else 'failed'

    return try_render_template("builds/build_info.html", bld_obj=bld_obj, container=container,
                               result=result)

