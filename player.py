import gi
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GLib, Gtk, GdkX11, GstVideo
import uvicorn
import threading
import time

app = FastAPI()
#https://akamaibroadcasteruseast.akamaized.net/cmaf/live/657078/akasource/out.mpd
#"file:///home/lapic/player/persistent-media-player-gstreamer-wrapper/PyGObject-Player/video_test.mp4"
#https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8

# Player initialization and backend methods
class Player:

    def __init__(self):
        Gst.init(None)

        # custom playbin pipeline
        self.playbin = Gst.parse_launch("playbin")

        if not self.playbin:
            sys.stderr.write("'playbin' gstreamer plugin missing\n")
            sys.exit(1)
        self.playbin.set_state(Gst.State.READY)
        self.status = Gst.State.READY
        
        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.bus_call)

        # creating GTK Window
        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_default_size(1, 1)
        self.window.connect("destroy", self.on_destroy)
        self.window.connect("size-allocate", self.on_size_allocate)
        self.window.set_keep_above(True)
        self.window.set_decorated(False)
        #self.window.fullscreen()

        # adding gtksink to pipeline for video output
        self.gtksink = Gst.ElementFactory.make("gtksink")
        self.playbin.set_property("video-sink", self.gtksink)

        self.video_area = self.gtksink.props.widget
        self.window.add(self.video_area)
        self.window.show_all()

    # This is used to check the status of the file being played
    def bus_call(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            sys.stdout.write("End-of-stream\n")
            self.changeState(Gst.State.NULL)

            #self.cust_func()
        
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print("Error While Playing: ", err)
            self.changeState(Gst.State.NULL)
        
            #self.cust_func()

    #change source
    def setUri(self, uri):
        self.changeState(Gst.State.NULL)
        self.playbin.set_property("uri", uri)
        self.current = uri

    def play(self):
        self.changeState(Gst.State.PLAYING)

    def pause(self):
        self.changeState(Gst.State.PAUSED)

    def stop(self):
        self.changeState(Gst.State.NULL)

    def changeState(self, state):
        self.playbin.set_state(state)
        self.status = state

    def getVolume(self):
        return self.playbin.get_property("volume")

    def setVolume(self, vol):
        # mapping vol from 0-1.0 to 0-10.0 but not required as audio will not be clear
        # vol = (vol)/(1.0)*(10.0)
        self.playbin.set_property("volume", vol)

    #temporary
    def updateConfig(self):
        self.config = {
                "state": "NULL",
                "duration": 0,
                "position": 0,
                "source": "NULL",
            }

        ret, current_state, pending_state = self.playbin.get_state(Gst.CLOCK_TIME_NONE)
        self.config['state'] = current_state.value_nick
         
        # not working ??
        uri = self.playbin.get_property("uri")
        self.config['source'] = uri if uri else None

        # Get the duration of the media
        success, duration = self.playbin.query_duration(Gst.Format.TIME)
        if success:
            self.config['duration'] = duration // Gst.SECOND  # Convert nanoseconds to seconds
        else:
            self.config['duration'] = None

        # Get the current position of the playback
        success, position = self.playbin.query_position(Gst.Format.TIME)
        if success:
            self.config['position'] = position // Gst.SECOND  # Convert nanoseconds to seconds
        else:
            self.config['position'] = None
        
        return self.config

    def getDuration(self):
        return self.playbin.query_duration(Gst.Format.TIME)

    def getPosition(self):
        return self.playbin.query_position(Gst.Format.TIME)

    def seek(self, location):
        self.playbin.seek_simple(Gst.Format.TIME,  Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, location * Gst.SECOND)

    def validateUri(self, uri):
        return Gst.uri_is_valid(uri)
    
    ###
    ## GTK
    ###
    def on_size_allocate(self, widget, allocation):
        self.window.resize(allocation.width, allocation.height)

    def on_destroy(self, widget):
        self.stop()
        Gtk.main_quit()

    def resize_window(self, width, height):
        self.window.resize(width, height)

    def move_window(self, x, y):
        self.window.move(x, y)

    def enter_fullscreen(self):
        self.window.fullscreen()

    def exit_fullscreen(self):
        self.window.unfullscreen()

player = Player()

# Define request models
class UriRequest(BaseModel):
    fileType: str
    locationType: str
    location: str

class NumberModel(BaseModel):
    value: float

class ResizeModel(BaseModel):
    x: int
    y: int
    w: int
    h: int

#API Endpoints
@app.get("/api/info")
async def info():
    return player.updateConfig()

@app.post("/api/source")
async def source(request: UriRequest):
    if player.validateUri(request.location):
        player.setUri(request.location)
        return 0
    else:
        raise HTTPException(status_code=422, detail="Invalid location type")
    
@app.post("/api/play")
async def play():
    player.play()
    return 0

@app.post("/api/pause")
async def pause():
    player.pause()
    return 0

@app.post("/api/stop")
async def stop():
    player.stop()
    return 0

@app.post("/api/volume")
async def volume(request: NumberModel):
    player.setVolume(request.value)
    return 0

@app.post("/api/seek")
async def seek(request: NumberModel):
    player.seek(request.value)
    return 0

@app.post("/api/resize")
async def resize(request: ResizeModel):
    player.resize_window(request.w, request.h)
    time.sleep(1)
    player.move_window(request.x, request.y)
    return 0

@app.post("/api/fullscreen")
async def fullscreen():
    player.enter_fullscreen()
    return 0

@app.post("/api/unfullscreen")
async def exit_fullscreen():
    player.exit_fullscreen()
    return 0


if __name__ == '__main__':
    def start_fastapi():
        uvicorn.run(app, host='0.0.0.0', port=1342)

    def start_gtk():
        Gtk.main()

    threading.Thread(target=start_fastapi).start()
    threading.Thread(target=start_gtk).start()



