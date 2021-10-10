FROM python:slim

COPY ./tumblr-to-vk-app ./tumblr-to-vk-app

WORKDIR tumblr-to-vk-app

CMD echo "Europe/Moscow" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata

RUN pip install -r requirements.txt

CMD ["python","-u","./main.py"]

#COPY api-serv.py ./

#ENTRYPOINT ["python", "./main.py"]

#EXPOSE 8099
