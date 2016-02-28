#!/usr/bin/env python
#coding=utf-8

import sys, os
from bottle import Bottle
from bottle import request
from bottle import response
from bottle import redirect
from bottle import MakoTemplate
from bottle import static_file
from bottle import abort
from beaker.cache import cache_managers
from toughradius.console.libs.paginator import Paginator
from toughradius.console.libs import utils
from toughradius.console.websock import websock
from toughradius.console import models
from toughradius.console.base import *
from toughradius.console.admin import forms
from hashlib import md5
from twisted.python import log
import bottle
import datetime
import json
import functools

__prefix__ = "/backup"

app = Bottle()
app.config['__prefix__'] = __prefix__


@app.route('/', apply=auth_opr)
def backup(db, render):
    backup_path = app.config.get('database.backup_path', '/var/toughradius/data')
    try:
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
    except:
        pass
    flist = os.listdir(backup_path)
    flist.sort(reverse=True)
    return render("sys_backup_db", backups=flist[:30], backup_path=backup_path)


@app.route('/dump', apply=auth_opr)
def backup_dump(db, render):
    from toughradius.tools.backup import dumpdb
    from toughradius.tools.config import find_config

    backup_path = app.config.get('database.backup_path', '/var/toughradius/data')
    backup_file = "toughradius_db_%s.json.gz" % utils.gen_backep_id()
    try:
        dumpdb(find_config(), os.path.join(backup_path, backup_file))
        return dict(code=0, msg="backup done!")
    except Exception as err:
        log.err()
        return dict(code=1, msg="backup fail! %s" % (err))


@app.post('/restore', apply=auth_opr)
def backup_restore(db, render):
    from toughradius.tools.backup import dumpdb, restoredb
    from toughradius.tools.config import find_config

    backup_path = app.config.get('database.backup_path', '/var/toughradius/data')
    backup_file = "toughradius_db_%s.before_restore.json.gz" % utils.gen_backep_id()
    rebakfs = request.params.get("bakfs")
    try:
        dumpdb(find_config(), os.path.join(backup_path, backup_file))
        restoredb(find_config(), os.path.join(backup_path, rebakfs))
        return dict(code=0, msg="restore done!")
    except Exception as err:
        return dict(code=1, msg="restore fail! %s" % (err))


@app.post('/delete', apply=auth_opr)
def backup_delete(db, render):
    backup_path = app.config.get('database.backup_path', '/var/toughradius/data')
    bakfs = request.params.get("bakfs")
    try:
        os.remove(os.path.join(backup_path, bakfs))
        return dict(code=0, msg="delete done!")
    except Exception as err:
        return dict(code=1, msg="delete fail! %s" % (err))


@app.route('/download/:path#.+#', apply=auth_opr)
def backup_download(path):
    backup_path = app.config.get('database.backup_path', '/var/toughradius/data')
    return static_file(path, root=backup_path, download=True, mimetype="application/x-gzip")


permit.add_route("/backup", u"备份管理", u"系统管理", is_menu=False, order=0.004, is_open=False)
