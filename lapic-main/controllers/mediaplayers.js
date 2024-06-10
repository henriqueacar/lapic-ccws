const { response } = require("../app");
var Errors = require("../models/errors");
const MediaPlayersModel = require("../models/mediaplayers");

const axios = require("axios");
//URL Wrapper
const apiUrl = "http://0.0.0.0:1342/api/";

/* URL CCWS
http://127.0.0.1:44642/dtv/mediaplayers/1
*/


exports.GETMediaPlayer = (req, res, next) => {
  //checa se o player id esta na lista
  const mediaPlayer = MediaPlayersModel.getMediaPlayerById(req.params.playerid);
  if (mediaPlayer.length === 0) {
    res.status(404).json(Errors.getError(101));
  }
  axios.get(apiUrl+"info")
        .then((response)=> {
          console.log("GET /api/info status:", response.status);
          res.json(response.data)
        })
        .catch(err => {
          console.error(err);
        });
};

/** /SOURCE 
 * 
   {
    "fileType": "mp4",
    "locationType": "localFile",
    "location": "/home/lapic/player/persistent-media-player-gstreamer-wrapper/videos/Channel_ID_5.1+4.mp4"
  }
*/

/**
 * estrutura para post
 {
    "url": "",
    "action": "",
    "pos": {"x": , "y": , "w": , "h": },
    "vol": "",
    "currTime": ""
}
 */

function sleep(ms) {
  return new Promise (resolve => setTimeout(resolve, ms));
}

exports.POSTMediaPlayer = async (req, res, next) => {
  //checa se o player id esta na lista
  const mediaPlayer = MediaPlayersModel.getMediaPlayerById(req.params.playerid);
  if (mediaPlayer.length === 0) {
    res.status(404).json(Errors.getError(101));
  } 

  //delay default para fazer a execucao esperar
  const defDelay = 500;

  //URL: string url, formatos mpd mp4
  const url = req.body.url;
  if (url !== undefined){
    //cria source para ser enviado ao wrapper e
    //checa formato mpd ou mp4
    const source = {
                      "fileType": "",
                      "locationType": "http",
                      "location": url
                    }
    if(url.endsWith('.mpd')){
      source.fileType = "dash"

      await axios.post(apiUrl+"source", source).then((response) => {
        console.log("POST /api/source status:", response.status);
      }).catch(err => {
        console.error(err);
      });
      await sleep(defDelay);
    }
    else if(url.endsWith('.mp4')){
      source.fileType = "mp4";
      source.locationType = "localFile";

      await axios.post(apiUrl+"source", source).then((response) => {
        console.log("POST /api/source status: ", response.status);
      }).catch(err => {
      console.error(err);
      });
      await sleep(defDelay);
    }
    else {
      //formato de arquivo nao suportado ou incorreto
      res.status(404).json(Errors.getError(101)
        .description.replace("[argumentName]", "'url'"));
        return;
    }
  } else {
    //url nao esta presente na requisicao, indefinido
  }

  //ACTION: string prepare start pause resume stop unload
  const action = req.body.action;
  if (action !== undefined){

    if(action === "start" || action === "resume"){
      axios.post(apiUrl+"play").then((response) => {
        console.log("POST /api/play status: ", response.status);
      }).catch(err => {
        console.error(err);
      });
      await sleep(defDelay);
    } 

    else if(action === "stop"){
      axios.post(apiUrl+"stop").then((response) => {
        console.log("POST /api/stop status:", response.status);
      }).catch(err => {
        console.error(err);
      });
      await sleep(defDelay);
    } 

    else if(action === "pause"){
      await axios.post(apiUrl+"pause").then((response) => {
        console.log("POST /api/pause status:", response.status);
      }).catch(err => {
        console.error(err);
      });
      await sleep(defDelay);
    } 

    else if(action === "prepare"){
      /*axios.post(apiUrl+" ").then((response) => {
        console.log("Prepare");
      });*/
    } 
    else if(action === "unload"){
      /*axios.post(apiUrl+" ").then((response) => {
        console.log("Unload");
      });*/
    } 

    else {
      //action definida incorretamente
      res.status(404).json(Errors.getError(101)
        .description.replace("[argumentName]", "'action'"));
      return;
    }
  } else {
    // action nao esta presente na requisicao, indefinido
  }
  
  //pos: integer x y w h
  const pos = req.body.pos;
  if(pos !== undefined) {
    if(pos.x < 0 || pos.y < 0 || pos.w < 0 || pos.h < 0) {
      res.status(404).json(Errors.getError(101)
        .description.replace("[argumentName]", "'pos'"));
      return;
    }

    const {x, y, h, w} = pos;
    const jsonResult = {x, y, h, w};

    await axios.post(apiUrl+"resize", jsonResult).then((response) => {
      //nao precisa responder
      console.log("POST /api/resize status: ", response.status);
    }).catch(err => {
      console.error(err);
    });
    await sleep(defDelay);
    return;
  } else {
    // pos nao esta presente na requisicao, indefinido
  }

  //vol: integer volume
  const vol = req.body.vol;
  if (vol !== undefined){
    if (vol < 0 || vol > 100){
      res.status(404).json(Errors.getError(101)
        .description.replace("[argumentName]", "'vol'"));
      return;
    }

  } else {
    //vol indefinido
  }

  //currTime: integer time in ms
  const currTime = req.body.currTime;
  if (currTime !== undefined){
    if(currTime < 0){
      res.status(404).json(Errors.getError(101)
        .description.replace("[argumentName]", "'currTime'"));
      return;
    }

    const jsonSeek = {
      "value": currTime/1000
    }
    
    await axios.post(apiUrl+"seek", jsonSeek).then((response) => {
      //nao precisa responder
      console.log("POST /api/seek status: ", response.status);
    }).catch(err => {
      console.error(err);
    });

  } else {
    //currTime indefinido
  }

  await sleep(1000);
  await axios.get(apiUrl+"info")
  .then((response)=> {
    console.log("GET /api/info status:", response.status);
    res.json(response.data)
  })
  .catch(err => {
    console.error(err);
  });

  await sleep(1000);
  console.log(" ")
};
