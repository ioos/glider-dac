FROM python:3.9

ARG glider_gid_uid=1000
RUN apt-get update && \
    apt-get -y install cron rsync libxml2-dev libudunits2-dev \
                       libnetcdf-dev netcdf-bin && \
    mkdir glider-dac && groupadd -g $glider_gid_uid glider && \
          useradd -u $glider_gid_uid -g $glider_gid_uid glider
ENV UDUNITS2_XML_PATH=/usr/share/xml/udunits
COPY . /glider-dac
# TODO: move logs elsewhere
VOLUME /glider-dac/logs/ /data /usr/local/lib/python3.8/site-packages/compliance_checker/data
WORKDIR /glider-dac
# not clear why reinstalling Mongo-related dependencies is necessary under
# Python 3, but this allows the service to run without import or runtime errors
RUN cd /usr/local/src && pip install -U pip && \
    pip install --no-cache Cython thredds_crawler numpy pytest && \
    pip install --no-cache -r /glider-dac/requirements.txt

RUN mkdir -p /data/submission /data/data/priv_erddap /data/data/pub_erddap \
             /erddapData/flag /erddapData/hardFlag  \
             /data/catalog/priv_erddap && \
    chown -R glider:glider /glider-dac /data /usr/local/lib/python3.9/site-packages/compliance_checker/data && \
    ln -sf /glider-dac/scripts/crontab /etc/crontab
USER glider
ENV PYTHONPATH="${PYTHONPATH:-}:/glider-dac"
ENV FLASK_APP=glider_dac:create_app

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "glider_dac:create_app()"]
