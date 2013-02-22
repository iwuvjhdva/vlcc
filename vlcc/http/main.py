# -*- coding: utf-8 -*-

import os

from datetime import datetime

from flask import Flask, render_template, send_from_directory, abort

from ..core import __version__
from ..core import initialize
from ..conf import config
from ..db import db, dict_factory


__all__ = ['main']


app = Flask(__name__)


# Images storage
@app.route('/static/img/<path:filename>')
def image(filename):
    image_dir = os.path.abspath(config['image_dir'])
    return send_from_directory(image_dir, filename)


@app.route('/')
def index():
    return comparison()


@app.route('/comparison/<comparison_id>')
def comparison(comparison_id=None):
    context = {}

    comparison = None

    # Fetching main menu

    db.row_factory()
    cursor = db.query(("SELECT c.id, c.movie, c.performed, "
                       "    GROUP_CONCAT(b.version, ' vs. ') AS versions "
                       "FROM comparison c, build b, comparison_build cb "
                       "WHERE c.id=cb.comparison_id "
                       "    AND b.version=cb.build_version "
                       "    AND c.ready=? "
                       "GROUP BY c.id "
                       "ORDER BY c.performed DESC"), [True])

    dt_format_from, dt_format_to = ('%Y-%m-%d %H:%M:%S',
                                    '%b %d %Y, %H:%M')

    menu = []
    for index, (comp_id, movie, performed, versions) in enumerate(cursor):
        menu_entry = {
            'id': comp_id,
            'versions': versions,
            'performed': (datetime
                          .strptime(performed, dt_format_from)
                          .strftime(dt_format_to)),
        }

        if (comparison_id is None and index == 0
                or unicode(comp_id) == comparison_id):
            menu_entry.update({
                'movie': movie,
                'is_active': True,
            })
            comparison = menu_entry

        menu.append(menu_entry)

    if menu:
        if comparison is None:
            abort(404)

        db.row_factory(dict_factory)
        # Fetching comparison overviews
        context['overviews'] = db.query(
            ("SELECT cb.build_version AS version, o.* "
             "FROM overview o, comparison_build cb "
             "WHERE o.comparison_build_id=cb.id "
             "    AND cb.comparison_id=? "
             "ORDER BY cb.build_version"),
            [comparison['id']])

    context.update({
        'version': __version__,
        'menu': menu,
        'comparison': comparison,
    })

    return render_template('comparison.html', **context)


def main():
    """VLCC HTTP server entry point.
    """

    # Initializing the core
    initialize(exit_func=lambda: abort(500))

    app.run()
