var express = require('express');

const MediaPlayerSchema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://gingacc-server-baseurl/mediaplayer.schema.json",
    "title": "MediaPlayer",
    "description": "A Media Player available in a DTVPlay-compliant TV set",
    "type": "object",
    "properties": {
        "id": {
            "description": "The unique identifier for a media player",
            "type": "integer"
        },
        "currentMedia": {
            "description": "URL for the media currently playing",
            "type": "string"
        },
        "state": {
            "description": "Current media player state (playing|paused|stopped|free)",
            "type": "string"
        },
        "transmissionSupported": {
            "description": "Supported protocols or transmission methods (pes|dsmcc|download|dash|hls)",
            "type": "array", "items": {"type": "string"},
        },
        "codecsSupported": {
            "description": "Supported media codecs",
            "type": "object",
            "properties": {
                "video": {
                    "description": "video codecs (H.264|H.265)",
                    "type": "array", "items": {"type": "string"}
                },
                "audio": {
                    "description": "audio codecs (AAC-LC|AAC-HE|AAC-HEV2|AC-3|E-AC-3|AC-4|MPEG-H)",
                    "type": "array", "items": {"type": "string"}
                },
                "subtitle": {
                    "description": "subtitle formats (IMSC1-TTML|WebVTT)",
                    "type": "array", "items": {"type": "string"}
                },
                "image": {
                    "description": "image formats (JPEG|PNG|GIF)",
                    "type": "array", "items": {"type": "string"}
                },
            },
        },
        "drmsSupported": {
            "description": "Supported DRM systems",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "systemld": {
                        "description": "DRM system unique identifier (defined by DASH-IF)",
                        "type": "string"
                    },
                    "drmName": {
                        "description": "DRM system name in lowercase, no spaces",
                        "type": "string"
                    },
                    "drmVersion": {
                        "description": "DRM system maximum version supported (major.minor)",
                        "type": "string"
                    },
                    "transmissionSupported": {
                        "description": "Supported protocols or transmission methods (pes|dsmcc|download|dash|hls)",
                        "type": "array", "items": {"type": "string"}
                    }
                }
            }
        },
        "pos": {
            "description": "Current screen positioning and dimensions",
            "type": "object",
            "properties": {
                "x": {
                    "description": "X coordinate for top left pixel",
                    "type": "number"
                },
                "y": {
                    "description": "Y coordinate for top left pixel",
                    "type": "number"
                },
                "w": {
                    "description": "Width in pixels",
                    "type": "number"
                },
                "h": {
                    "description": "Height in pixels",
                    "type": "number"
                },
            },
        },
        "vol": {
            "description": "Current sound volume 0-100",
            "type": "number",
            "minimum": 0,
            "maximum": 100
        },
        "currTime": {
            "description": "Current play time in milliseconds",
            "type": "number"
        },
        "duration": {
            "description": "Duration of cuurent media in milliseconds",
            "type": "number"
        },
    },
    "required": [ "id", "currentMedia", "state" ]
};

const mediaPlayers = {
    "players": [
        {
            "id": "1",
            "currentMedia": "http://ott.broadcaster.com/movie/id3564",
            "state": "playing",
            "transmissionSupported": ["download", "dash", "hls"],
            "codecsSupported": {
                "video": ["H.264", "H.265"],
                "audio": ["AAC-HEv2", "MPEG-H"]
            },
            "pos": {"x": 0, "y": 0, "w": 1920, "h": 1080},
            "vol": "100",
            "currTime": "2345221",
            "duration": "13456320"
        },
        {
            "id": "2",
            "currentMedia": null,
            "state": "free",
            "transmissionSupported": ["dsmcc", "pes"],
            "codecsSupported": {
                "video": ["H.264", "H.265"],
                "audio": ["AAC-HEv2", "MPEG-H"],
                "subtitles": ["WebVTT"]
            },
        },
        {
            "id": "3",
            "currentMedia": null,
            "state": "free",
            "transmissionSupported": ["download", "dsmcc"],
            "codecsSupported": {
                "image": ["JPEG", "GIF", "PNG"],
            },
        }
    ]
}

exports.getMediaPlayers = () => {
    return mediaPlayers;
};

exports.getMediaPlayerById = (id) => {
    return mediaPlayers.players.filter(players => players.id == id);
};