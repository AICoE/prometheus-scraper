FROM docker.io/centos/python-36-centos7:latest

ADD app.py /
ADD requirements.txt /

RUN pip install -r /requirements.txt

CMD [ "python", "/app.py"]
