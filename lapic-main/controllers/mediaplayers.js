const { response } = require("../app");
var Errors = require("../models/errors");
const MediaPlayersModel = require("../models/mediaplayers");

const axios = require("axios");
const apiUrl = "http://0.0.0.0:1342/api/";

/** /INFO */
exports.GETMediaPlayers = (req, res, next) => {
  axios.get(apiUrl+"info")
  .then((response)=> res.json(response.data));
};

/** /SOURCE 
 * 
   {
    "fileType": "mp4",
    "locationType": "localFile",
    "location": "/home/lapic/player/persistent-media-player-gstreamer-wrapper/videos/Channel_ID_5.1+4.mp4"
  }
*/
exports.POSTMediaSource = (req, res, next) => {
  axios.post(apiUrl+"source", req.body).then((response) => 
  res.json(response.data));
  console.log(req.body);
};

/** /PLAY */
exports.POSTPlayMedia = (req, res, next) => {
  axios.post(apiUrl+"play").then((response) => {
    res.json((response.data));
  });
};

/** /STOP */
exports.POSTStopMedia = (req, res, next) => {
  axios.post(apiUrl+"stop").then((response) => {
    res.json((response.data));
  });
};


/*exports.GETMediaPlayers = (req, res, next) => {
  const mediaPlayers = MediaPlayersModel.getMediaPlayers();
  res.json(mediaPlayers);
};

exports.GETMediaPlayer = (req, res, next) => {
  const mediaPlayer = MediaPlayersModel.getMediaPlayerById(req.params.playerid);
  if (mediaPlayer.length === 0) {
    res.status(404).json(Errors.getError(101));
  } else res.json(mediaPlayer[0]);
};*/

exports.GETMediaPlayer = (req, res, next) => {
  //checa se o player id esta na lista
  const mediaPlayer = MediaPlayersModel.getMediaPlayerById(req.params.playerid);
  if (mediaPlayer.length === 0) {
    res.status(404).json(Errors.getError(101));
  }
  axios.get(apiUrl+"info")
        .then((response)=> {
          res.json(response.data)
        })
        .catch(err => {
          console.error(err);
        });
};

exports.POSTMediaPlayer = (req, res, next) => {
  //checa se o player id esta na lista
  const mediaPlayer = MediaPlayersModel.getMediaPlayerById(req.params.playerid);
  if (mediaPlayer.length === 0) {
    res.status(404).json(Errors.getError(101));
  } 

  //url: string url
  const url = req.body.url;
  if (url !== undefined){

  } else {
    //url indefinido
  }

  //action: string prepare start pause resume stop unload
  const action = req.body.action;
  if (action !== undefined){
    if(action === "start"){
      axios.post(apiUrl+"play").then((response) => {
        console.log("Play");
      });
    } else if(action === "stop"){
      axios.post(apiUrl+"stop").then((response) => {
        console.log("Stop");
      });
    } else {
      //action definida incorretamente
      console.log("Action nao definida corretamente");
      res.json("Action nao definida corretamente");
      return;
    }
  } else {
    // erro action indefinido
  }
  
  //pos: integer x y w h
  const pos = req.body.pos;
  if(pos !== undefined) {
    const posX = req.body.pos.x;
    const posY = req.body.pos.y;
    const posW = req.body.pos.w;
    const posH = req.body.pos.h;
  } else {
    // pos indefinido
  }

  //vol: integer volume
  const vol = req.body.vol;
  if (vol !== undefined){

  } else {
    //vol indefinido
  }

  //currTime: integer time in ms
  const currTime = req.body.currTime;
  if (currTime !== undefined){

  } else {
    //currTime indefinido
  }

  axios.get(apiUrl+"info")
        .then((response)=> {
          res.json(response.data)
        })
        .catch(err => {
          console.error(err);
        });
};
