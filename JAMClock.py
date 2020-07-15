#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   JAMClock.py por:
#   Flavio Danesse <fdanesse@gmail.com>
#   CeibalJAM! - Uruguay

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gi
gi.require_version('Gtk', '3.0')
from Main import Main
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity import activity
from pygame.locals import *
from sugargame import event
from sugargame import canvas
import sugargame
from sugar3.graphics.style import GRID_CELL_SIZE
import pygame
import socket
import sys
from gi.repository import Gtk, GObject, Gdk
import os


class JAMClock(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle, False)
        self.set_title('JAMClock')
        # self.set_toolbox(activity.ActivityToolbox(self))

        w = Gdk.Screen.width()
        h = Gdk.Screen.height() - 1 * GRID_CELL_SIZE

        # Start the Game activity
        self.game = Main((w, h))

        # Build the Pygame canvas and start the game running
        # (self.game.run is called when the activity constructor
        # returns).
        self._pygamecanvas = canvas.PygameCanvas(
            self, main=self.game.run, modules=[pygame.display])

        # Note that set_canvas implicitly calls read_file when
        # resuming from the Journal.

        self._pygamecanvas.set_size_request(w, h)
        self.set_canvas(self._pygamecanvas)
        self._pygamecanvas.grab_focus()

        # Build the activity toolbar.
        self.build_toolbar()

    def build_toolbar(self):
        self.toolbar_box = ToolbarBox()
        self.activity_button = ActivityToolbarButton(self)
        self.toolbar_box.toolbar.insert(self.activity_button, 0)
        self.activity_button.show()

        self._separator = Gtk.SeparatorToolItem()
        self._separator.props.draw = False
        self._separator.set_expand(True)
        self.toolbar_box.toolbar.insert(self._separator, -1)
        self._separator.show()

        self.stop = StopButton(self)
        self.toolbar_box.toolbar.insert(self.stop, -1)
        self.stop.show()
        
        self.set_toolbar_box(self.toolbar_box)
        self.toolbar_box.show_all()
        return self.toolbar_box

    def get_run_game(self):
        raise NotImplementedError
        pass

    def salir(self, widget):
        lambda w: Gtk.main_quit()
        sys.exit()


# -----------------------------------------------
# 	******** El Juego en Gtk ********
# -----------------------------------------------


class VentanaGTK(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, Gtk.WINDOW_TOPLEVEL)
        self.set_title("JAMClock")
        # self.fullscreen()
        self.set_size_request(800, 600)
        self.socket = Gtk.Socket()
        self.add(self.socket)
        self.ventana = None

        self.add_events(Gdk.ALL_EVENTS_MASK)
        self.connect("destroy", self.salir)
        self.connect("set-focus-child", self.refresh)
        self.show_all()

    def refresh(self, widget, datos):
        try:
            pygame.display.update()
        except:
            pass
        self.queue_draw()
        return True

    def salir(self, widget):
        pygame.quit()
        sys.exit()
