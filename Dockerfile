FROM python:3.9

# Variables
ENV TINI_VERSION=v0.14.0 \
    TINI_SHA256=eeffbe853a15982e85d923390d3a0c4c5bcf9c78635f4ddae207792fa4d7b5e6 \
    CYSO_CA_SHA256=a8b86b5a4ee70cb08ee7c475fb4f43b922483adca41a591ba16d9cb4db78178c \
    REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt" \
    PIP_INDEX_URL="https://pypi.build.cyso.net/pip/live" \
    PYTHONWARNINGS="ignore:Unverified HTTPS request"

# Install Tini
RUN curl -fSL -o /sbin/tini https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini \
 && echo "${TINI_SHA256} */sbin/tini" | sha256sum -c - \
 && chmod +x /sbin/tini
ENTRYPOINT [ "/sbin/tini", "--" ]

# Install Cyso CA bundle
RUN curl -fSL -o cyso-internal-ca.deb http://apt.cyso.net/cyso-internal-ca.deb \
 && echo "${CYSO_CA_SHA256} *cyso-internal-ca.deb" | sha256sum -c - \
 && dpkg -i cyso-internal-ca.deb \
 && rm cyso-internal-ca.deb

# Install dependencies
ADD requirements.txt /usr/src/app/
RUN pip install --upgrade pip setuptools virtualenv tox \
 && pip install -r /usr/src/app/requirements.txt

# Add application
WORKDIR /usr/src/app
COPY . /usr/src/app

# Install application
RUN python setup.py develop --no-deps

CMD [ "./docker-entrypoint.sh" ]
