#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Frakkup - setup.py
# Copyright (C) 2014  Yudy Chen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup

setup(name='frakkup',
      version='0.1.0',
      description='Incremental Backup Tool Based on Rsync.',
      author='Yudy Chen',
      author_email='yudychen@gmail.com',
      url='https://github.com/oneleaftea/frakkup',
     # package_dir={'bin':''},
      scripts=['frakkup.py'],
     # data_files=[''],
      requires=['gi.repository.Gtk', 'gi.repository.Vte', 'gi.repository.GLib', 'gi.repository.GObject','threading', 're', 'os', 'time', 'configparser.SafeConfigParser', 'datetime.datetime', 'subprocess'],
     )
