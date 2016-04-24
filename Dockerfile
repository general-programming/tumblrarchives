FROM gliderlabs/alpine:edge

# Update packages and install setup requirements.
RUN apk --update upgrade && \
	apk add python python-dev py-pip py-flask py-gevent py-gunicorn py-httplib2 py-sqlalchemy py-psycopg2 py-oauth2 py-mako gcc musl-dev postgresql-dev ca-certificates && \
	update-ca-certificates && \
	rm -rf /var/cache/apk/*

# Set WORKDIR to /src
WORKDIR /src

# Add and install Python modules
ADD requirements.txt /src/requirements.txt
RUN pip install -r requirements.txt

# Bundle app source
ADD . /src

# Install main module
RUN python setup.py install

# Expose web port
EXPOSE 5000

# Command
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-k", "gevent", "-w", "4", "archives:app"]