#FROM python:3.12

#ARG glider_gid_uid=1000
#COPY . /glider-dac
#ENV UDUNITS2_XML_PATH=/usr/share/xml/udunits
#RUN apt-get update && \
#    apt-get -y install libxml2-dev netcdf-bin rsync && \
#    cd /usr/local/src && pip install -U pip && \
#    pip install --no-cache -r /glider-dac/requirements.txt && \
#    apt-get -y remove libxml2-dev && rm -rf /var/lib/apt/lists/*
# TODO: move logs elsewhere
#VOLUME /glider-dac/logs/ /data /usr/local/lib/python3.13/site-packages/compliance_checker/data
#WORKDIR /glider-dac
#RUN mkdir -p /data/submission /data/data/priv_erddap /data/data/pub_erddap \
#             /erddapData/flag /erddapData/hardFlag  \
#             /data/catalog/priv_erddap
#ENV PYTHONPATH="${PYTHONPATH:-}:/glider-dac"
#ENV FLASK_APP=glider_dac:create_app
#
#EXPOSE 5000
#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "glider_dac:create_app()"]


FROM python:3.11

ARG glider_gid_uid=1000
COPY . /glider-dac

ENV UDUNITS2_XML_PATH=/usr/share/xml/udunits/udunits2.xml

RUN echo "Python version: $(python --version)" && pip debug --verbose

# Install system dependencies
RUN apt-get update && \
    apt-get -y install libxml2-dev libudunits2-dev netcdf-bin rsync && \
    pip install -U pip

# Install cf-units FIRST (valid version, with source fallback)
RUN pip install cf-units==3.2.0

# Now install the rest of your app requirements
RUN pip install --no-cache -r /glider-dac/requirements.txt

# Clean up
RUN apt-get -y remove libxml2-dev libudunits2-dev && rm -rf /var/lib/apt/lists/*

# Volume and working directories
VOLUME /glider-dac/logs/ /data /usr/local/lib/python3.11/site-packages/compliance_checker/data

WORKDIR /glider-dac

RUN mkdir -p /data/submission /data/data/priv_erddap /data/data/pub_erddap \
             /erddapData/flag /erddapData/hardFlag  \
             /data/catalog/priv_erddap

ENV PYTHONPATH="/glider-dac"
ENV FLASK_APP=glider_dac:create_app

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "glider_dac:create_app()"]