FROM python:slim

ARG ARG_TIMEZONE=Europe/Moscow

ENV ENV_TIMEZONE ${ARG_TIMEZONE}

COPY ./tumblr-to-vk-app ./tumblr-to-vk-app

WORKDIR tumblr-to-vk-app

# sync timezone
RUN echo '$ENV_TIMEZONE' > /etc/timezone \
    && ln -fsn /usr/share/zoneinfo/$ENV_TIMEZONE /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && pip install -r requirements.txt

ENTRYPOINT ["python","-u","./main.py"]

#COPY api-serv.py ./

#ENTRYPOINT ["python", "./main.py"]

#EXPOSE 8099
