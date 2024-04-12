FROM python:3.8

ARG glider_gid_uid=1000
RUN apt-get update && \
    apt-get -y install cron rsync libxml2-dev libudunits2-dev \
                       libnetcdf-dev netcdf-bin libsqlite3-mod-spatialite && \
    mkdir glider-dac && groupadd -g $glider_gid_uid glider && \
          useradd -u $glider_gid_uid -g $glider_gid_uid glider
COPY . /glider-dac
# TODO: move logs elsewhere
VOLUME /glider-dac/logs/ /data
WORKDIR glider-dac
# not clear why reinstalling Mongo-related dependencies is necessary under
# Python 3, but this allows the service to run without import or runtime errors
RUN pip install -U pip && \
    pip install --no-cache Cython thredds_crawler numpy pytest && \
    pip install --no-cache -r requirements.txt

RUN mkdir -p /data/submission /data/data/priv_erddap /data/data/pub_erddap \
             /erddapData/flag /erddapData/hardFlag berkeleydb \
             /data/catalog/priv_erddap && \
    chown -R glider:glider /glider-dac /data && \
    ln -sf /glider-dac/scripts/crontab /etc/crontab
USER glider
ENV PYTHONPATH="${PYTHONPATH}:/glider-dac"

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "glider_dac:create_app()"]
