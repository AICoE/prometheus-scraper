FROM python:3

ADD app.py /
ADD requirements.txt /

RUN pip install -r requirements.txt

CMD [ "python", "./app.py" ]
