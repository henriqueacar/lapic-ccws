# Copyright 2023 Fraunhofer IIS
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the Player Adapter), to 
# deal in the Software without restriction, including without limitation the 
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# IABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.


from fastapi import FastAPI, Body, Request, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
import xml.etree.ElementTree as ET
from websockets.sync.client import connect

from threading import Thread
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib
Gst.init(None)

Gst.debug_set_active(True)
Gst.debug_set_default_threshold(1)

class GlobalStateMiddleware:

    def __init__(self):
        self.main_loop = GLib.MainLoop()
        thread = Thread(target=self.main_loop.run)
        thread.start()

        self.pipeline = Gst.parse_launch("queue name=queue ! decodebin name=decodebin ! uimanager name=ui ! hpi ! audioconvert name=audioconvert ! volume name=volume ! audioresample ! autoaudiosink queue name=video_queue ! decodebin name=videodec ! videoconvert ! autovideosink")
        self.pipeline.get_by_name("decodebin").connect("autoplug-select", self.autoplug_callback, 'data')
        self.queue = self.pipeline.get_by_name("queue")
        self.video_queue = self.pipeline.get_by_name("video_queue")
        self.ui = self.pipeline.get_by_name("ui")
        
        self.state = None
        self.config = None
        self.uuid = ""

        self.format = Gst.Format(Gst.Format.TIME)
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)


    async def __call__(self, request: Request, call_next):
        request.state.uuid = self.uuid
        request.state.pipeline = self.pipeline
        request.state.main_loop = self.main_loop
        request.state.queue = self.queue
        request.state.video_queue = self.video_queue
        request.state.ui = self.ui
        request.state.format = self.format
        request.state.config = self.config
        request.state.pad_callback = self.pad_callback
        request.state.update_config = self.update_config

        if (self.pipeline.get_by_name("source") == None):
            request.state.source = ""
        else:
            request.state.source = self.pipeline.get_by_name("source").get_property("location")

        if (self.pipeline.get_state(1).state == Gst.State.PLAYING):
            request.state.state = "PLAYING"
        if (self.pipeline.get_state(1).state == Gst.State.PAUSED):
            request.state.state = "PAUSED"
        if (self.pipeline.get_state(1).state == Gst.State.NULL):
            request.state.state = "NULL"
        if (self.pipeline.get_state(1).state == Gst.State.READY):
            request.state.state = "READY"
        
        request.state.duration = self.pipeline.query_duration(self.format).duration / Gst.SECOND
        request.state.current_position = self.pipeline.query_position(self.format).cur / Gst.SECOND

        response = await call_next(request)
        return response

    def config_init(self, attrib):
        self.uuid = attrib['uuid']
        self.config = {
                "state": "NULL",
                "duration": 0,
                "position": 0,
                "source": 0,
                "drc": {
                    "effecttype": set(),
                },
                "nga": {
                    "preset": {},
                    "audioobject": {},
                    "audioobjectwitch" : {}
                }
            }

    def update_elem_switch(self, elem_switch):
        self.config['nga']['audioobjectwitch'][elem_switch.attrib['id']] = {}
        self.config['nga']['audioobjectwitch'][elem_switch.attrib['id']] = elem_switch.attrib
        self.config['nga']['audioobjectwitch'][elem_switch.attrib['id']]['audioobject'] = {}
        for child in elem_switch:
            if child.tag == "audioElements":
                for element in child:
                    self.config['nga']['audioobjectwitch'][elem_switch.attrib['id']]['audioobject'][element.attrib['id']] = element.attrib
                    for custom_kind in element:
                        self.config['nga']['audioobjectwitch'][elem_switch.attrib['id']]['audioobject'][element.attrib['id']].update(custom_kind.attrib)
            else:
                self.config['nga']['audioobjectwitch'][elem_switch.attrib['id']][child.tag] = child.attrib

    def update_elem(self, elem):
        self.config['nga']['audioobjectwitch']['audioobject'][elem.attrib['id']] = elem.attrib
        for child in elem:
            self.config['nga']['audioobjectwitch'][child.tag] = child.attrib
            for custom_kind in child:
                self.config['nga']['audioobjectwitch'][elem_switch.attrib['id']]['audioobject'][element.attrib['id']].update(custom_kind.attrib)

    def update_preset(self, preset):
        self.config['nga']['preset'][preset.attrib['id']] = preset.attrib
        for customKind in preset:
            for description in customKind:
                self.config['nga']['preset'][preset.attrib['id']]["description"] = description.text
                self.config['nga']['preset'][preset.attrib['id']]["langCode"] = description.attrib["langCode"]

    def update_config(self, xmlstr):
        tree = ET.ElementTree(ET.fromstring(xmlstr))
        root = tree.getroot()

        if self.config is None:
            self.config_init(root.attrib)

        for child in root:

            if (child.tag == "DRCInfo"):
                for effect in child:
                    self.config['drc']["effecttype"].add(effect.attrib["index"])

            if (child.tag == "presets"):
                for preset in child:
                    self.update_preset(preset)

            if (child.tag == "audioElementSwitch"):
                self.update_elem_switch(child)

            if (child.tag == "audioElements"):
                self.update_elem(child)
    
    def on_message(self, bus, message):
        addr = "ws://localhost:8765"
        if ((message.type == Gst.MessageType.APPLICATION)):
            self.update_config(message.get_structure().get_value("config"))
            with connect(addr) as websocket:
                websocket.send("config changed")
                answer = websocket.recv()

        if ((message.type == Gst.MessageType.STATE_CHANGED)):
            if (self.state != self.pipeline.get_state(1).state):
                self.state = self.pipeline.get_state(1).state
                with connect(addr) as websocket:
                    websocket.send("state changed")
                    answer = websocket.recv()
                
        if ((message.type == Gst.MessageType.EOS)):
            with connect(addr) as websocket:
                websocket.send("eos")
                answer = websocket.recv()

        if ((message.type == Gst.MessageType.ERROR)):
            with connect(addr) as websocket:
                websocket.send("error")
                answer = websocket.recv()

    def autoplug_callback(self, bin, pad, caps, factory, data):    
        if (factory.get_name() == 'qtdemux') or (factory.get_name() == 'h264parse') or (factory.get_name() == 'h265parse'):
            return 0
        else:
            return 1

    def pad_callback(self, demuxer, pad):
        if 'video' in pad.get_property("template").name_template:
            pad.link(self.video_queue.pads[0])
        if 'audio' in pad.get_property("template").name_template:
            pad.link(self.queue.pads[0])



app = FastAPI()
middleware = GlobalStateMiddleware()
app.add_middleware(BaseHTTPMiddleware, dispatch=middleware)

def wait_async_message(pipeline, message):
    while (message == Gst.StateChangeReturn.ASYNC):
        message = pipeline.get_state(10)
    if (message == Gst.StateChangeReturn.SUCCESS):
        return "State changed successfully"
    elif ((message.state == Gst.State.READY) | (message.state == Gst.State.PLAYING)):
        return "State changed successfully"
    else:
        return "ERROR occurued"
    
def check_range(value, gt, lt):
    if (value.value < lt): return True
    if (value.value > gt): return True
    return False

class SourceModel(BaseModel):
    fileType: str
    locationType: str
    location: str

class NumberModel(BaseModel):
    value: float

def create_number_model(min_value: float, max_value: float):
    return NumberModel(value=Field(..., gt=min_value, lt=max_value))

class IntegerModel(BaseModel):
    value: int

class StringModel(BaseModel):
    value: str

class BoolModel(BaseModel):
    value: bool

class ResizeModel(BaseModel):
    x: int
    y: int
    w: int
    h: int

@app.get("/api/info")
async def info(request: Request):
    if (request.state.config == None):
        return "Config has not been created yet"
    request.state.config['source'] = request.state.source
    request.state.config['duration'] = request.state.duration
    request.state.config['position'] = request.state.current_position
    request.state.config['state'] = request.state.state
    return request.state.config

@app.post("/api/seek")
async def play(request: Request, number: NumberModel = Body(...)):
    pipeline = request.state.pipeline
    if (request.state.config == None):
        raise HTTPException(status_code=422, detail="The stream has not been configured yet")

    if (number.value < 0):
        raise HTTPException(status_code=422, detail="Seeking position must pe positive")

    if (number.value > request.state.duration):
        raise HTTPException(status_code=422, detail="Seeking position should not exceed the file duration")  

    pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, number.value * Gst.SECOND)  

    return 0

@app.post("/api/source")
async def play(request: Request, source: SourceModel = Body(...)):
    pipeline = request.state.pipeline
    if source.locationType == 'http':
        src = Gst.ElementFactory.make("souphttpsrc", "source")
    elif source.locationType == 'localFile':
        src = Gst.ElementFactory.make("filesrc", "source")
    else:
        raise HTTPException(status_code=422, detail="Invalid location type")
    
    if source.fileType == 'dash':
        demux = Gst.ElementFactory.make("dashdemux", "demux")
    elif source.fileType == 'mp4':
        demux = Gst.ElementFactory.make("qtdemux", "demux")
    else:
        raise HTTPException(status_code=422, detail="Invalid file type")

    pipeline.add(demux)
    demux.connect("pad-added", request.state.pad_callback)

    src.set_property("location", source.location)
    pipeline.add(src)
    src.link(demux)

    return 0

##
#RESIZE WINDOW
##
@app.post("/api/resize")
async def resize(request: Request, resize: ResizeModel = Body(...)):
    VideoCrop = Gst.ElementFactory.make('videocrop', 'VideoCrop')
    VideoCrop.set_property('top', 100)
    VideoCrop.set_property('bottom', 100)
    VideoCrop.set_property('left', 50)
    VideoCrop.set_property('right', 150)
    return resize

##
#CHANGE VOLUME
##
@app.post("/api/volume")
async def volume(request: Request, volume_level: NumberModel = Body(...)):
    volume_element = request.state.pipeline.get_by_name("volume")
    if volume_element:
        volume_element.set_property("volume", volume_level.value)
        return 0
    return "Volume change not available"

@app.post("/api/ready")
async def play(request: Request):
    message = request.state.pipeline.set_state(Gst.State.READY)
    return wait_async_message(request.state.pipeline, message)

@app.post("/api/play")
async def play(request: Request):
    message = request.state.pipeline.set_state(Gst.State.PLAYING)
    return wait_async_message(request.state.pipeline, message)

@app.post("/api/pause")
async def pause(request: Request):
    message = request.state.pipeline.set_state(Gst.State.PAUSED)
    return wait_async_message(request.state.pipeline, message)

@app.post("/api/stop")
async def stop(request: Request):
    message = request.state.pipeline.set_state(Gst.State.NULL)
    return wait_async_message(request.state.pipeline, message)

@app.post("/api/reset")
async def reset(request: Request):
    return 0

@app.post("/api/drc/effecttype")
async def set_drc_effecttype(request: Request, number: StringModel = Body(...)):
    if (number.value in request.state.config['drc']['effecttype']):
        uuid = request.state.uuid
        xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{10}" paramInt="{number.value}" paramFloat="{0}" />'
        request.state.ui.set_property('ui-event', xmlstr)
        return 0
    else:
        raise HTTPException(status_code=422, detail="Invalid effect value")

@app.post("/api/drc/targetloudness")
async def set_drc_targetloudness(request: Request, number: NumberModel = Body(...)):
    uuid = request.state.uuid
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{20}" paramInt="{0}" paramFloat="{number.value}" />'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/preset")
async def set_nga_preset(request: Request, preset_id: StringModel = Body(...)):
    if not preset_id.value in request.state.config['nga']['preset']:
        raise HTTPException(status_code=422, detail="Invalid preset id")
    
    if (request.state.config['nga']['preset'][preset_id.value] == {}):
        raise HTTPException(status_code=422, detail="Invalid preset id")

    uuid = request.state.uuid
    paramInt = preset_id.value
    actionType = "30"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{paramInt}" />'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/audioobject/{id}/mute")
async def set_nga_audioobject_mute(request: Request, id: str, boolean: BoolModel = Body(...)):
    if not id in request.state.config['nga']['audioobject']:
        raise HTTPException(status_code=422, detail="Invalid audio object id")
    
    if (request.state.config['nga']['audioobject'][id] == {}):
        raise HTTPException(status_code=422, detail="Invalid audio object id")

    uuid = request.state.uuid
    actionType = "40"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{id}" paramBool="{boolean.value}"/>'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/audioobject/{id}/prominence")
async def set_nga_audioobject_prominence(request: Request, id: str, number: NumberModel = Body(...)):
    if not id in request.state.config['nga']['audioobject']:
        raise HTTPException(status_code=422, detail="Invalid audio object id")
    
    if (request.state.config['nga']['audioobject'][id] == {}):
        raise HTTPException(status_code=422, detail="Invalid audio object id")
    
    if ('prominenceLevelProp' not in request.state.config['nga']['audioobject'][id]):
        raise HTTPException(status_code=422, detail="Prominence change not allowed")

    if (check_range(number, float(request.state.config['nga']['audioobject'][id]['prominenceLevelProp']["max"]), float(request.state.config['nga']['audioobject'][id]['prominenceLevelProp']["min"]))):
        raise HTTPException(status_code=422, detail="Value is out of range")

    uuid = request.state.uuid
    actionType = "41"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{id}" paramFloat="{number.value}"/>'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/audioobject/{id}/azimuth")
async def set_nga_audioobject_azimuth(request: Request, id: str, number: NumberModel = Body(...)):
    if not id in request.state.config['nga']['audioobject']:
        raise HTTPException(status_code=422, detail="Invalid audio object id")
    
    if (request.state.config['nga']['audioobject'][id] == {}):
        raise HTTPException(status_code=422, detail="Invalid audio object id")

    if ('azimuthProp' not in request.state.config['nga']['audioobject'][id]):
        raise HTTPException(status_code=422, detail="Azimuth change not allowed")
    
    if (check_range(number, float(request.state.config['nga']['audioobject'][id]['azimuthProp']["max"]), float(request.state.config['nga']['audioobject'][id]['azimuthProp']["min"]))):
        raise HTTPException(status_code=422, detail="Value is out of range")

    uuid = request.state.uuid
    actionType = "42"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{id}" paramFloat="{number.value}"/>'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/audioobject/{id}/elevation")
async def set_nga_audioobject_elevation(request: Request, id: str, number: NumberModel = Body(...)):
    if not id in request.state.config['nga']['audioobject']:
        raise HTTPException(status_code=422, detail="Invalid audio object id")
    
    if (request.state.config['nga']['audioobject'][id] == {}):
        raise HTTPException(status_code=422, detail="Invalid audio object id")

    if ('elevationProp' not in request.state.config['nga']['audioobject'][id]):
        raise HTTPException(status_code=422, detail="Elevation change not allowed")
    
    if (check_range(number, float(request.state.config['nga']['audioobject'][id]['elevationProp']["max"]), float(request.state.config['nga']['audioobject'][id]['elevationProp']["min"]))):
        raise HTTPException(status_code=422, detail="Value is out of range")

    uuid = request.state.uuid
    actionType = "43"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{id}" paramFloat="{number.value}"/>'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/audioobjectswitch/{id}")
async def set_nga_audioobjectswitch(request: Request, id: str, element_id: StringModel = Body(...)):
    if not id in request.state.config['nga']['audioobjectwitch']:
        raise HTTPException(status_code=422, detail="Invalid switch group id")
    
    if (request.state.config['nga']['audioobjectwitch'][id] == {}):
        raise HTTPException(status_code=422, detail="Invalid switch group id")
    
    if not element_id.value in request.state.config['nga']['audioobjectwitch'][id]['audioobject']:
        raise HTTPException(status_code=422, detail="Invalid element id")
    
    if (request.state.config['nga']['audioobjectwitch'][id]['audioobject'][element_id.value] == {}):
        raise HTTPException(status_code=422, detail="Invalid element id")

    uuid = request.state.uuid
    actionType = "60"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{id}" paramFloat="{element_id.value}"/>'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/audioobjectswitch/{id}/mute")
async def set_nga_audioobjectswitch_mute(request: Request, id: str, boolean: BoolModel = Body(...)):
    if not id in request.state.config['nga']['audioobjectwitch']:
        raise HTTPException(status_code=422, detail="Invalid switch group id")
    
    if (request.state.config['nga']['audioobjectwitch'][id] == {}):
        raise HTTPException(status_code=422, detail="Invalid switch group id")

    uuid = request.state.uuid
    actionType = "61"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{id}" paramBool="{boolean.value}"/>'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/audioobjectswitch/{id}/prominence")
async def set_nga_audioobjectswitch_prominence(request: Request, id: str, number: NumberModel = Body(...)):
    if not id in request.state.config['nga']['audioobjectwitch']:
        raise HTTPException(status_code=422, detail="Invalid switch group id")
    
    if (request.state.config['nga']['audioobjectwitch'][id] == {}):
        raise HTTPException(status_code=422, detail="Invalid switch group id")

    if ('prominenceLevelProp' not in request.state.config['nga']['audioobjectwitch'][id]):
        raise HTTPException(status_code=422, detail="Prominence change not allowed")

    if (check_range(number, float(request.state.config['nga']['audioobjectwitch'][id]['prominenceLevelProp']["max"]), float(request.state.config['nga']['audioobjectwitch'][id]['prominenceLevelProp']["min"]))):
        raise HTTPException(status_code=422, detail="Value is out of range")

    uuid = request.state.uuid
    actionType = "62"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{id}" paramFloat="{number.value}"/>'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/audioobjectswitch/{id}/azimuth")
async def set_nga_audioobjectswitch_azimuth(request: Request, id: str, number: NumberModel = Body(...)):
    if not id in request.state.config['nga']['audioobjectwitch']:
        raise HTTPException(status_code=422, detail="Invalid switch group id")
    
    if (request.state.config['nga']['audioobjectwitch'][id] == {}):
        raise HTTPException(status_code=422, detail="Invalid switch group id")

    if ('azimuthProp' not in request.state.config['nga']['audioobjectwitch'][id]):
        raise HTTPException(status_code=422, detail="Azimuth change not allowed")
    
    if (check_range(number, float(request.state.config['nga']['audioobjectwitch'][id]['azimuthProp']["max"]), float(request.state.config['nga']['audioobjectwitch'][id]['azimuthProp']["min"]))):
        raise HTTPException(status_code=422, detail="Value is out of range")

    uuid = request.state.uuid
    actionType = "63"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{id}" paramFloat="{number.value}"/>'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/nga/audioobjectswitch/{id}/elevation")
async def set_nga_audioobjectswitch_elevation(request: Request, id: str, number: NumberModel = Body(...)):
    if not id in request.state.config['nga']['audioobjectwitch']:
        raise HTTPException(status_code=422, detail="Invalid switch group id")
    
    if (request.state.config['nga']['audioobjectwitch'][id] == {}):
        raise HTTPException(status_code=422, detail="Invalid switch group id")

    if ('elevationProp' not in request.state.config['nga']['audioobjectwitch'][id]):
        raise HTTPException(status_code=422, detail="Elevation change not allowed")
    
    if (check_range(number, float(request.state.config['nga']['audioobjectwitch'][id]['elevationProp']["max"]), float(request.state.config['nga']['audioobjectwitch'][id]['elevationProp']["min"]))):
        raise HTTPException(status_code=422, detail="Value is out of range")

    uuid = request.state.uuid
    actionType = "64"
        
    xmlstr = f'<ActionEvent uuid="{uuid}" version="9.0" actionType="{actionType}" paramInt="{id}" paramFloat="{number.value}"/>'
    request.state.ui.set_property('ui-event', xmlstr)
    return 0

@app.post("/api/uilanguage")
async def set_uilanguage(string: StringModel = Body(...)):
    pass

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=1342)
