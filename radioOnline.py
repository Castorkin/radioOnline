# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 14:51:56 2015

@author: castor
"""

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import GObject
import sqlite3

import os
import signal
import argparse

Gst.init()
signal.signal(signal.SIGINT, signal.SIG_DFL)
GObject.threads_init()    
    

class RadioWindow():
    '''
    def __init__(self,player):
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.box = Gtk.Box(spacing=6)
        self.window.add(self.box)
        #self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy_event)
        self.window.set_border_width(10)
        self.buttonPlay = Gtk.Button('Play')
        self.buttonPlay.connect("clicked", self.playRadio,player)
        self.buttonStop = Gtk.Button('Stop')
        self.buttonStop.connect("clicked", self.stopRadio,player)
        self.box.pack_start(self.buttonPlay, True, True, 0)
        self.box.pack_start(self.buttonStop, True, True, 0)
        self.buttonPlay.show()
        self.buttonStop.show()
        self.box.show()
        self.window.show()
    '''
    def __init__(self):
        self.gladefile = "gladeRadio.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("mainWindow")
        #self.buttonPlay = self.builder.get_object("playButton")
        #self.buttonPlay.connect("clicked", self.playRadio,player)
        radioURI = 'http://nashe1.hostingradio.ru:80/nashe-128.mp3'       
        self.player = self.playerMaker(radioURI)
        self.mainWindowBus = self.player.pipeline.get_bus()
        self.mainWindowBus.add_signal_watch()
        self.mainWindowBus.connect('message', self.titleChange)
        self.buttonStop = self.builder.get_object("stopButton")
        #self.buttonStop.connect("clicked", self.stopRadio,player)
        self.adjustmentVolume = self.builder.get_object("volumeAdjustment")
        #elf.adjustmentVolume.connect("value_changed", self.volumeAdjustment_changed, player)
        self.title = self.builder.get_object("label1")
        #self.title.connect("button_press_event",self.titleChange, player)
        self.con = sqlite3.connect('test.db')
        self.window.show()
    def playerMaker(self,source):
        return Player(source)
    def on_mainWindow_destroy(self, object, data=None):
        print "quit with cancel"
        self.con.close()
        Gtk.main_quit()
    def on_gtk_quit_activate(self,menuitem, data=None):
        print "quit from menu"
        self.con.close()
        Gtk.main_quit()
    def quit_event(self,widget,data=None):
        print "quit from menu"
        Gtk.main_quit()
    
    def destroy_event(self, widget, data=None):
        print "quit with cancel"
        Gtk.main_quit()
    #def delete_event(self,widget,data=None):
    #    return False
    def main(self):
        Gtk.main()
    def emptyFunction(self,button):
        pass
    def playRadio(self,button):
        print 'playing start'
        self.player.volumeControl(self.adjustmentVolume.get_value())
        self.player.play()
        playTitle = self.player.playingTitles()
        #i=0
        #while i<0:
            #print player.playList 
            #print player.playingTitles()
            #i+=1
        self.builder.get_object("label1").set_text(playTitle)
    def stopRadio(self,widget):
        print 'playing stop'
        print self.player.playingTitles()
        self.player.stop()
        
    def volumeAdjustment_changed(self,adjustment):
        volumeLevel = self.adjustmentVolume.get_value()
        self.player.volumeControl(volumeLevel)
    
    def test(self, label, text):
        print 'test'
    
    def setStation(self,evBox,evButton):
        print 'now playing station'
        print Gtk.Builder.get_object(self.builder,Gtk.Buildable.get_name(evBox)).get_children()[0].get_label()
        #label.set_property('visible',False)
    
    def titleChange(self,bus,message):
        struct = message.get_structure()
        if message.type == Gst.MessageType.TAG and message.parse_tag() and struct.has_field('taglist'):
            #print 'GStreamer find meta-tags'
            taglist = struct.get_value('taglist')
            
            for x in range(taglist.n_tags()):
                name = taglist.nth_tag_name(x)
                if name=='title':
                    self.title.set_text(taglist.get_string(name)[1])

class Player():
    
    playingTitle = ''
    def __init__(self,location):
        self.pipeline = self.create_pipeline(location)
        
        message_bus = self.pipeline.get_bus()
        message_bus.add_signal_watch()
        message_bus.connect('message', self.message_handler)
        
        #self.pipeline.get_by_name('volume').set_property('volume', args.volume / 100.)
    def playingTitles(self):
        return self.playingTitle
    def create_source(self, location):
        if location.startswith('http'):
            source = Gst.ElementFactory.make('souphttpsrc', 'source')
        elif os.path.exists(location):
            source = Gst.ElementFactory.make('filesrc', 'source')
        else:
            raise IOError("source must starts with http")
        source.set_property('location', location)
        return source
    def pipeLineGet(self):
        return self.pipeline()
    def create_pipeline(self, location):
        pipeline = Gst.Pipeline()
        source = self.create_source(location)
        decodebin = Gst.ElementFactory.make('decodebin', 'decodebin')
        audioconvert = Gst.ElementFactory.make('audioconvert', 'audioconvert')
        volume = Gst.ElementFactory.make('volume', 'volume')
        audiosink = Gst.ElementFactory.make('autoaudiosink', 'autoaudiosink')

        def on_pad_added(decodebin, pad):
            pad.link(audioconvert.get_static_pad('sink'))
        decodebin.connect('pad-added', on_pad_added)
        
        [pipeline.add(k) for k in [source, decodebin, audioconvert, volume, audiosink]]
        
        source.link(decodebin)
        audioconvert.link(volume)
        volume.link(audiosink)
        
        return pipeline
        
    def volumeControl(self, vLevel):
        self.pipeline.get_by_name('volume').set_property('volume',vLevel/100.0)
    
    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)
    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)
    
    def message_handler(self,bus, message):
        struct = message.get_structure()
        if message.type == Gst.MessageType.TAG and message.parse_tag() and struct.has_field('taglist'):
            #print 'GStreamer find meta-tags'
            taglist = struct.get_value('taglist')
            '''
            if taglist.get_string('title')[1]:
                print taglist.nth_tag_name('title')
            '''
            
            for x in range(taglist.n_tags()):
                name = taglist.nth_tag_name(x)
                if name=='title':
                    print ' now playing %s'%(taglist.get_string(name)[1])
                    self.playingTitle = taglist.get_string(name)[1]
                    
                    
            
        else:
            pass

class args():
    location = 'http://nashe1.hostingradio.ru:80/nashe-128.mp3'
    #volume = 10
 
if __name__ == "__main__":
    player1 = Player(args.location)
    #player1.play()
    #player1.volumeLevel(50)
    #Gtk.main()
    rWind = RadioWindow()
    rWind.main()