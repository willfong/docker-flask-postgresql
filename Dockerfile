FROM tiangolo/uwsgi-nginx-flask:python3.7
ENV STATIC_INDEX 1
ENV STATIC_URL /
ENV STATIC_PATH /app/app/static
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
