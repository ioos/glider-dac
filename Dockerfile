FROM python:3.11

ARG glider_gid_uid=1000
COPY . /glider-dac

ENV UDUNITS2_XML_PATH=/usr/share/xml/udunits/

# Install system dependencies
RUN apt-get update && \
    apt-get -y install libxml2-dev libudunits2-dev netcdf-bin rsync && \
    pip install -U pip && \
    pip install cf-units==3.2.0 && \
    pip install --no-cache -r /glider-dac/requirements.txt && \
    apt-get -y remove libxml2-dev libudunits2-dev && rm -rf /var/lib/apt/lists/*

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
