# Instruções

Abrir o terminal na pasta:
```sh
home/lapic-ccws
```
Executar o player:
```sh
python3 player.pi
```

Agora o player estará ouvindo na url:
```sh
http://0.0.0.0:1342 
```

# Endpoints 
## GET
```sh
http://0.0.0.0:1342/api/info
```

## POST

### api/source
```sh
http://0.0.0.0:1342/api/source
```
Requisição esperada:
```sh
   {
    "fileType": "",
    "locationType": "",
    "location": ""
  }
```
Location deve ser a URI do arquivo a ser tocado. Para arquivos locais, necessário incluir "file:///" no início da URI. Restante das variáveis não importa, existem apenas por questão de compatibilidade com o CC-WS. 

### api/play
```sh
http://0.0.0.0:1342/api/play
```

### api/pause
```sh
http://0.0.0.0:1342/api/pause
```

### api/stop
```sh
http://0.0.0.0:1342/api/stop
```

### api/volume
```sh
http://0.0.0.0:1342/api/volume
```
Requisição esperada:
```sh
{
    "value": 0<=X<=1
}
```

### api/seek
```sh
http://0.0.0.0:1342/api/seek
```
Requisição esperada:
```sh
{
    "value": tempo em segundos
}
```

### api/resize
```sh
http://0.0.0.0:1342/api/resize
```
Requisição esperada:
```sh
{
    "x": coordenada x
    "y": coordenada y
    "w": largura da janela
    "h": altura da janela
}
```


### api/fullscreen
```sh
http://0.0.0.0:1342/api/fullscreen
```
Coloca a janela em fullscreen.

### api/unfullscreen
```sh
http://0.0.0.0:1342/api/unfullscreen
```
Tira a janela do fullscreen.
