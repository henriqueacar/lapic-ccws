var express = require('express');
var MediaPlayersController = require('../controllers/mediaplayers');
var router = express.Router();

/* Media player API */
/* 8.5.2 */
router.get('/', MediaPlayersController.GETMediaPlayer);

/* 8.5.3 */
router.get('/:playerid', MediaPlayersController.GETMediaPlayer);

/* 8.5.4 */
router.post('/:playerid', MediaPlayersController.POSTMediaPlayer);
/* */

module.exports = router;
