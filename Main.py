#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   Main.py por:
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
from gi.repository import Gtk
import pygame, gc, sys, os, threading, random
from pygame.locals import *

gc.enable()

RESOLUCION = (800, 600)
SEPARADOR = 5
ARCHIVO= os.path.join(os.environ["HOME"], "jamclockconfig.txt")

import BiblioJAM
from BiblioJAM.JAMButton import JAMButton
from BiblioJAM.JAMLabel import JAMLabel
from BiblioJAM.JAMDialog import JAMDialog
from BiblioJAM.JAMClock import JAMClock
from BiblioJAM.JAMCalendar import JAMCalendar
import BiblioJAM.JAMGlobals as JAMG

def Guardar(tiempo):
	archivo= open(ARCHIVO, "w")
	archivo.write(tiempo)
	archivo.close()
	os.chmod(ARCHIVO, 0666)

def Abrir():
	tiempo= "12:00"
	if os.path.exists(ARCHIVO):
		archivo= open(ARCHIVO, "r")
		tiempo= archivo.read()
		archivo.close()
	return tiempo

def Traduce_posiciones(VA, VH):
	eventos= pygame.event.get(pygame.MOUSEBUTTONDOWN)
	for event in eventos:
		x, y = event.pos
		xx= x/VA
		yy= y/VH
		event_pos= (xx, yy)
	for event in eventos:
		evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos= event_pos, button=event.button)
		pygame.event.post(evt)

	eventos= pygame.event.get(pygame.MOUSEMOTION)
	for event in eventos:
		x, y = event.pos
		xx= x/VA
		yy= y/VH
		event_pos= (xx, yy)
	for event in eventos:
		evt = pygame.event.Event(pygame.MOUSEMOTION, pos= event_pos, rel=event.rel, buttons=event.buttons)
		pygame.event.post(evt)

class Main():
	def __init__(self, res):
		self.resolucionreal= res
		self.ventana= None
		self.name= "JAMClock"
		self.ventana_real= None
		self.VA= None
		self.VH= None

		# Variables del Juego
		self.fondo= None
		self.reloj= None
		self.estado= False

		self.sonidoalarma= None
		self.duracionalarma= None
		self.jamclock= None
		self.jamcalendar= None
		self.cerrar= None
		self.controlalarma= None
		self.controles= None

		self.mensaje= None
		self.dialog= None

		self.preset()
		self.load()
		self.run()

	def preset(self):
		pygame.display.set_mode( (0,0), pygame.DOUBLEBUF | pygame.FULLSCREEN, 0)
		A, B= RESOLUCION
		self.ventana= pygame.Surface( (A, B), flags=HWSURFACE )
		self.ventana_real= pygame.display.get_surface()
		C, D= (0,0)
		if self.resolucionreal:
			C, D= self.resolucionreal
		else:
			C= pygame.display.Info().current_w
			D= pygame.display.Info().current_h
			self.resolucionreal= (C,D)
		self.VA= float(C)/float(A)
		self.VH= float(D)/float(B)

	def load(self):
		pygame.event.set_blocked([JOYAXISMOTION, JOYBALLMOTION, JOYHATMOTION, JOYBUTTONUP, JOYBUTTONDOWN])
		pygame.event.set_allowed([MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN, KEYDOWN, KEYUP, VIDEORESIZE,
			VIDEOEXPOSE, USEREVENT, QUIT, ACTIVEEVENT])
		pygame.mouse.set_visible(True)

		a,b,c= JAMG.get_estilo_papel_quemado()
		if not self.reloj: self.reloj= pygame.time.Clock()
		if not self.fondo: self.fondo= self.get_fondo(color= b)

		if not self.dialog:
			self.dialog= JAMDialog()
			self.dialog.set_text(tamanio= 24)
			d,e,f= JAMG.get_estilo_celeste()
			self.dialog.set_colors_dialog(base= e, bordes= f)
			self.dialog.set_colors_buttons(colorbas= a, colorbor= b, colorcara= c)
			self.dialog.set_text_buttons(tamanio=24)

		if not pygame.mixer.get_init():
			pygame.mixer.init(44100, -16, 2, 2048)
		pygame.mixer.music.set_volume(1.0)

		if not self.controles: self.controles= pygame.sprite.OrderedUpdates()
		if not self.cerrar:
			self.cerrar= JAMButton("", JAMG.get_icon_exit())
			self.cerrar.set_imagen(origen= JAMG.get_icon_exit(), tamanio=(20,20))
			self.cerrar.set_tamanios(tamanio= (0,0), grosorbor= 1, espesor= 1)
			self.cerrar.set_colores(colorbas= a, colorbor= b, colorcara= c)
			x= RESOLUCION[0] - self.cerrar.get_tamanio()[0]
			self.cerrar.set_posicion(punto= (x, 0))
			self.cerrar.connect(callback= self.selecciona_mensaje_salir)
		if not self.jamclock:
			self.jamclock= JAMClock()
			self.jamclock.set_tamanios(2)
			self.jamclock.set_colors_base(c, a)
			y= self.cerrar.get_tamanio()[1] + SEPARADOR
			self.jamclock.set_posicion(punto= (SEPARADOR, y))
			self.sonidoalarma= JAMG.get_alarma_reloj1()
			self.duracionalarma= 30
		if not self.jamcalendar:
			self.jamcalendar= JAMCalendar()
			self.jamcalendar.set_gama_colors(colorselect= a, colorbor= b, colorcara= c)
			self.jamcalendar.set_text(tamanio= 24)
			x= RESOLUCION[0] - self.jamcalendar.get_tamanio()[0] - SEPARADOR
			y= self.cerrar.get_tamanio()[1] + SEPARADOR
			self.jamcalendar.set_posicion(punto= (x, y))
		if not self.controlalarma:
			self.controlalarma= ControlAlarma()
			x,y= self.jamcalendar.get_posicion()
			w,h= self.jamcalendar.get_tamanio()
			x= x + w/2 - self.controlalarma.get_tamanio()[0]/2
			y += h + SEPARADOR*5
			self.controlalarma.set_posicion(punto= (x, y))
			self.controlalarma.boton_active.connect(callback= self.active_alarma)

		self.controles.add(self.jamclock)
		self.controles.add(self.jamcalendar)
		self.controles.add(self.cerrar)
		self.controles.add(self.controlalarma)
		self.load_conf()

		self.estado= True

	def load_conf(self):
		alarma= Abrir()
		alarma= alarma.split(":")
		self.controlalarma.horas= int(alarma[0])
		self.controlalarma.minutos= int(alarma[1])
		self.controlalarma.etiqueta_tiempo.set_text(texto= "%s:%s" % (self.controlalarma.horas, self.controlalarma.minutos))
		self.active_alarma(None)

	def active_alarma(self, button= None):
		horas, minutos= self.controlalarma.get_time()
		if self.controlalarma.active:
			self.jamclock.set_alarma((100,100), self.sonidoalarma, self.duracionalarma)
			self.controlalarma.set_active(False)
		elif not self.controlalarma.active:
			self.jamclock.set_alarma((horas, minutos), self.sonidoalarma, self.duracionalarma)
			self.controlalarma.set_active(True)
			Guardar("%s:%s" % (horas, minutos))

	def run(self):
		self.ventana.blit(self.fondo, (0,0))
		self.controles.draw(self.ventana)
		pygame.display.update()
		while self.estado:
			self.reloj.tick(35)
			while Gtk.events_pending():
			    	Gtk.main_iteration(False)
			Traduce_posiciones(self.VA, self.VH)
			if self.mensaje:
				self.pause_game()
			self.controles.clear(self.ventana, self.fondo)
			self.controles.update()
			self.handle_event()
			pygame.event.clear()
			self.controles.draw(self.ventana)			
			self.ventana_real.blit(pygame.transform.scale(self.ventana, self.resolucionreal), (0,0))
			pygame.display.update()

	def handle_event(self):
		for event in pygame.event.get(pygame.KEYDOWN):
			tecla= event.key
			if tecla== pygame.K_ESCAPE:
				pygame.event.clear()
				return self.selecciona_mensaje_salir()

	def pause_game(self):
		while self.mensaje.sprites():
			self.reloj.tick(35)
			while Gtk.events_pending():
			    	Gtk.main_iteration(False)
			Traduce_posiciones(self.VA, self.VH)
			self.controles.clear(self.ventana, self.fondo)
			self.mensaje.clear(self.ventana, self.fondo)
			self.mensaje.update()
			pygame.event.clear()
			self.controles.draw(self.ventana)
			self.mensaje.draw(self.ventana)
			self.ventana_real.blit(pygame.transform.scale(self.ventana, self.resolucionreal), (0,0))
			pygame.display.update()

	def deselecciona_mensaje(self, boton):
		self.mensaje= pygame.sprite.OrderedUpdates()

	def selecciona_mensaje_salir(self, button= None):
		self.dialog.set_text(texto= "¿ Salir de JAMClock ?")
		self.dialog.connect(funcion_ok= self.salir, funcion_cancel= self.deselecciona_mensaje)
		self.mensaje= self.dialog

	def get_fondo(self, color=(100,100,100,1), tamanio=RESOLUCION):
		superficie = pygame.Surface( tamanio, flags=HWSURFACE )
		superficie.fill(color)
		img= pygame.image.load("firma.png")
		ww, hh= RESOLUCION
		w,h= img.get_size()
		x= ww/2 - w/2
		y= hh- h - SEPARADOR
		superficie.blit(img, (x,y))
		return superficie

	def salir(self, boton):
		sys.exit()

sep= 5
class ControlAlarma(pygame.sprite.OrderedUpdates):
	def __init__(self):
		pygame.sprite.OrderedUpdates.__init__(self)
		self.base= None
		self.etiqueta= None
		self.etiqueta_tiempo= None

		self.boton_active= None
		self.botonminutos_down= None
		self.botonminutos_up= None
		self.botonhoras_down= None
		self.botonhoras_up= None

		self.active= False
		self.horas= 12
		self.minutos= 00

		self.load()

		self.botonminutos_up.connect(callback= self.next)
		self.botonminutos_down.connect(callback= self.back)

		self.botonhoras_up.connect(callback= self.nexthoras)
		self.botonhoras_down.connect(callback= self.backhoras)

	def set_active(self, valor):
		if valor:
			self.active= True
			self.boton_active.set_imagen(origen= JAMG.get_icon_ok(), tamanio=(20,20))
		elif not valor:
			self.active= False
			self.boton_active.set_imagen(origen= JAMG.get_icon_cancel(), tamanio=(20,20))

	def next(self, button= None):
		if self.minutos >= 59:
			self.minutos= 0
			self.horas+= 1
		elif self.minutos < 59:
			self.minutos+= 1
		if self.horas >= 24:
			self.horas= 0
		self.etiqueta_tiempo.set_text(texto= "%s:%s" % (self.horas, self.minutos))
		self.set_active(False)

	def back(self, button= None):
		if self.minutos <= 1:
			self.minutos= 59
			self.horas-= 1
		elif self.minutos > 0:
			self.minutos-= 1
		if self.horas < 0:
			self.horas= 23
		self.etiqueta_tiempo.set_text(texto= "%s:%s" % (self.horas, self.minutos))
		self.set_active(False)

	def nexthoras(self, button= None):
		if self.horas >= 23:
			self.horas= 0
		elif self.horas < 23:
			self.horas+= 1
		self.etiqueta_tiempo.set_text(texto= "%s:%s" % (self.horas, self.minutos))
		self.set_active(False)

	def backhoras(self, button= None):
		if self.horas <= 23 and self.horas > 0:
			self.horas-= 1
		elif self.horas <= 0:
			self.horas= 23
		self.etiqueta_tiempo.set_text(texto= "%s:%s" % (self.horas, self.minutos))
		self.set_active(False)

	def load(self):
		a,b,c= JAMG.get_estilo_papel_quemado()
		self.etiqueta= Etiqueta("Alarma")
		self.etiqueta.set_colores(colorbas= a, colorbor= b, colorcara= c)
		self.etiqueta.set_tamanios(tamanio= (0, 0), grosorbor= 1, espesor= 1)
		self.etiqueta.set_text(tamanio= 24)

		self.etiqueta_tiempo= Etiqueta("%s:%s" % (self.horas, self.minutos))
		self.etiqueta_tiempo.set_tamanios(tamanio= (0, 0), grosorbor= 1, espesor= 1)
		self.etiqueta_tiempo.set_text(tamanio= 40)

		self.botonminutos_down= JAMButton("", "down.png")
		self.botonminutos_down.set_imagen(origen= "down.png", tamanio=(20,20))
		self.botonminutos_down.set_colores(colorbas= a, colorbor= b, colorcara= c)
		self.botonminutos_down.set_tamanios(tamanio= (0, 0), grosorbor= 1, espesor= 1)

		self.botonminutos_up= JAMButton("", "up.png")
		self.botonminutos_up.set_imagen(origen= "up.png", tamanio=(20,20))
		self.botonminutos_up.set_colores(colorbas= a, colorbor= b, colorcara= c)
		self.botonminutos_up.set_tamanios(tamanio= (0, 0), grosorbor= 1, espesor= 1)

		self.botonhoras_down= JAMButton("", "down.png")
		self.botonhoras_down.set_imagen(origen= "down.png", tamanio=(20,20))
		self.botonhoras_down.set_colores(colorbas= a, colorbor= b, colorcara= c)
		self.botonhoras_down.set_tamanios(tamanio= (0, 0), grosorbor= 1, espesor= 1)

		self.botonhoras_up= JAMButton("", "up.png")
		self.botonhoras_up.set_imagen(origen= "up.png", tamanio=(20,20))
		self.botonhoras_up.set_colores(colorbas= a, colorbor= b, colorcara= c)
		self.botonhoras_up.set_tamanios(tamanio= (0, 0), grosorbor= 1, espesor= 1)

		self.boton_active= JAMButton("", JAMG.get_icon_ok())
		self.boton_active.set_imagen(origen= JAMG.get_icon_ok(), tamanio=(20,20))
		self.boton_active.set_colores(colorbas= a, colorbor= b, colorcara= c)
		self.boton_active.set_tamanios(tamanio= (0, 0), grosorbor= 1, espesor= 1)

		self.base= self.get_base(color= b, tamanio= self.geometria())
		w= self.get_tamanio()[0] - sep*2
		self.etiqueta_tiempo.set_tamanios(tamanio= (w, 0), grosorbor= 1, espesor= 1)
		self.add([self.base, self.etiqueta, self.etiqueta_tiempo, self.botonminutos_up, self.botonminutos_down,
			self.botonhoras_up, self.botonhoras_down, self.boton_active])
		self.set_posicion(punto= (0,0))

	def geometria(self):
		ancho, alto= (200,130)
		return (ancho, alto)

	def get_base(self, color=(100,100,100,1), tamanio= (100, 100)):
		base= pygame.sprite.Sprite()
		superficie= pygame.Surface( tamanio, flags=HWSURFACE )
		superficie.fill(color)
		base.image= superficie
		base.rect= base.image.get_rect()
		return base
		
	def set_posicion(self, punto= (0,0)):
		x, y= punto
		self.base.rect.x, self.base.rect.y= (x,y)
		x+= sep
		y+= sep

		# ---
		xx= self.base.rect.x + self.base.rect.w/2 - self.etiqueta.get_tamanio()[0]/2
		self.etiqueta.set_posicion(punto= (xx, y))

		y+= self.etiqueta.get_tamanio()[1] + sep
		xx= self.base.rect.x + self.base.rect.w/2 - self.etiqueta_tiempo.get_tamanio()[0]/2
		self.etiqueta_tiempo.set_posicion(punto= (xx, y))	
		# ---

		x,y= self.etiqueta_tiempo.get_posicion()
		xx,hh= self.botonminutos_up.get_tamanio()
		x+= self.etiqueta_tiempo.get_tamanio()[0] - self.botonminutos_up.get_tamanio()[0]
		y-= self.botonminutos_up.get_tamanio()[1] - self.etiqueta_tiempo.get_tamanio()[1]/2
		self.botonminutos_up.set_posicion(punto= (x, y))

		x,y= self.botonminutos_up.get_posicion()
		y+= self.botonminutos_up.get_tamanio()[1]
		self.botonminutos_down.set_posicion(punto= (x, y))

		x,y= self.etiqueta_tiempo.get_posicion()
		xx,hh= self.botonhoras_up.get_tamanio()
		y-= self.botonhoras_up.get_tamanio()[1] - self.etiqueta_tiempo.get_tamanio()[1]/2
		self.botonhoras_up.set_posicion(punto= (x, y))

		x,y= self.botonhoras_up.get_posicion()
		y+= self.botonhoras_up.get_tamanio()[1]
		self.botonhoras_down.set_posicion(punto= (x, y))

		x,y= self.etiqueta_tiempo.get_posicion()
		w,h= self.etiqueta_tiempo.get_tamanio()
		ww,yy= self.boton_active.get_tamanio()
		x+= w/2 - ww/2
		y+= sep + h
		self.boton_active.set_posicion(punto= (x, y))

	def get_tamanio(self):
		return (self.base.rect.w, self.base.rect.h)

	def get_time(self):
		return (self.horas, self.minutos)
		
class Etiqueta(JAMButton):
	def __init__(self, texto):
		JAMButton.__init__(self, texto, None)
	def update(self):
		pass

