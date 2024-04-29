FROM node:18

WORKDIR /usr/src/app

ARG NODE_ENV
ENV NODE_ENV $NODE_ENV

COPY package.json /usr/src/app/
RUN npm install

COPY . /usr/src/app

ENV GINGACCWSPORT 44642
EXPOSE $GINGACCWSPORT
CMD [ "npm", "start" ]
