FROM python:3.8.3-alpine

# create directory for the app user
RUN mkdir -p /home/app
ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONUNBUFFERED 1

# create the app user
RUN addgroup -S app && adduser -S app -G app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME 
RUN mkdir $APP_HOME/static
RUN mkdir $APP_HOME/media 
WORKDIR $APP_HOME
# install dependencies
RUN apk update && apk add libpq postgresql-dev \
	&& apk add --virtual build-deps gcc \
	python3-dev musl-dev jpeg-dev zlib-dev libffi-dev

COPY ./requirements.txt . 

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --ignore-installed
RUN apk add libjpeg

# copy entrypoint.sh
COPY ./entrypoint.sh $APP_HOME

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "app.wsgi:application"]

# run entrypoint.sh
ENTRYPOINT ["/home/app/web/entrypoint.sh"]