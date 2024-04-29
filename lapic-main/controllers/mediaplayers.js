const { response } = require("../app");
var Errors = require("../models/errors");
const MediaPlayersModel = require("../models/mediaplayers");

const axios = require("axios");
const apiUrl = "http://0.0.0.0:1342/api/";

/*const apiUrl = "http://0.0.0.0:1342/api/info/";

axios.get(apiUrl).then((response) => {
  console.log(response);
});*/
/*
exports.GETMediaPlayers = () => {
  const res = axios.get(apiUrl+"info/").then((response)=> {
    console.log(response.data);
  });
};*/

exports.GETMediaPlayers = (req, res, next) => {
  axios.get(apiUrl+"info/")
  .then((response)=> res.json(response.data));
};

/*
"fileType": "mp4",
"locationType": "localFile",
"location": "/home/lapic/player/persistent-media-player-gstreamer-wrapper/videos/Channel_ID_5.1+4.mp4"    
*/

const dados = {
  fileType: 'mp4',
  locationType: 'localFile',
  location: '/home/lapic/player/persistent-media-player-gstreamer-wrapper/videos/Channel_ID_5.1+4.mp4'
}


exports.POSTMediaSource = (req, res, next) => {
  axios.post(apiUrl+"source/", 
  {
    "fileType": "mp4",
    "locationType": "localFile",
    "location": "/home/lapic/player/persistent-media-player-gstreamer-wrapper/videos/Channel_ID_5.1+4.mp4"
  }).then((response) => 
  res.json(response.data));
};

exports.POSTPlayMedia = () => {
  axios.post(apiUrl+"play/").then((response) => {

  });
};

exports.POSTStopMedia = () => {
  axios.post(apiUrl+"stop/").then((response) => {

  });
};


/*exports.GETMediaPlayers = (req, res, next) => {
  const mediaPlayers = MediaPlayersModel.getMediaPlayers();
  res.json(mediaPlayers);
};*/

exports.GETMediaPlayer = (req, res, next) => {
  const mediaPlayer = MediaPlayersModel.getMediaPlayerById(req.params.playerid);
  if (mediaPlayer.length === 0) {
    res.status(404).json(Errors.getError(101));
  } else res.json(mediaPlayer[0]);
};

exports.POSTMediaPlayer = (req, res, next) => {
  const mediaPlayer = MediaPlayersModel.getMediaPlayerById(req.params.playerid);
  if (mediaPlayer.length === 0) {
    res.status(404).json(Errors.getError(101));
  } else {
    const postedMediaPlayer = req.body;
    console.log("Call RemotePlayer: ", postedMediaPlayer);
    /* RemotePlayer communication and update code */
    res.json(mediaPlayer[0]);
  }
};
