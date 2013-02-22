# -*- coding: utf-8 -*-

import os

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

    # Loading menu
    db.row_factory()

    cursor = db.query(("SELECT c.id, c.performed, "
                       "    GROUP_CONCAT(b.version, ', ') AS versions "
                       "FROM comparison c, build b, comparison_build cb "
                       "WHERE c.id=cb.comparison_id "
                       "    AND b.version=cb.build_version "
                       "    AND c.ready=? "
                       "GROUP BY c.id "
                       "ORDER BY c.performed DESC"), [True])

    menu = [{
        'id': cid,
        'title': versions,
        'is_active': comparison_id == unicode(cid),
    } for cid, performed, versions in cursor]

    comparison = None

    if menu:
        if comparison_id is None:
            comparison_id = menu[0]['id']

        db.row_factory(dict_factory)

        # Loading comparison
        cursor = db.query(("SELECT c.*, "
                           "    GROUP_CONCAT(b.version, ', ') AS versions "
                           "FROM comparison c, build b, comparison_build cb "
                           "WHERE cb.comparison_id=c.id "
                           "    AND cb.build_version=b.version "
                           "    AND c.id=? AND c.ready=?"
                           "GROUP BY c.id"),
                          [comparison_id, True])
        comparison = cursor.fetchone()

        if comparison is None:
            abort(404)

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
