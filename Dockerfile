#ENV TAG=3.10-slim
ARG TAG=slim
ARG IMAGE=balenalib/aarch64-alpine-python

FROM $IMAGE
#FROM python:$TAG

ARG ARG_TIMEZONE=Europe/Moscow

ENV ENV_TIMEZONE ${ARG_TIMEZONE}

COPY ./tumblr-to-vk-app ./tumblr-to-vk-app

WORKDIR tumblr-to-vk-app

# sync timezone
RUN apk add tzdata \
    && cp /usr/share/zoneinfo/$ENV_TIMEZONE /etc/localtime \
    && echo "$ENV_TIMEZONE" >  /etc/timezone \
    && pip install -r requirements.txt
#RUN echo '$ENV_TIMEZONE' > /etc/timezone \
#    && ln -fsn /usr/share/zoneinfo/$ENV_TIMEZONE /etc/localtime \
#    && dpkg-reconfigure --frontend noninteractive tzdata \
#    && pip install -r requirements.txt

ENTRYPOINT ["python","-u","./main.py"]

#COPY api-serv.py ./

#ENTRYPOINT ["python", "./main.py"]

#EXPOSE 8099
