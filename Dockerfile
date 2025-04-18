FROM python:3.8

ARG glider_gid_uid=1000
RUN apt-get update && \
    apt-get -y install cron rsync libxml2-dev libudunits2-dev \
                       libnetcdf-dev netcdf-bin && \
    mkdir glider-dac && groupadd -g $glider_gid_uid glider && \
          useradd -u $glider_gid_uid -g $glider_gid_uid glider
COPY . /glider-dac
# TODO: move logs elsewhere
VOLUME /glider-dac/logs/ /data /usr/local/lib/python3.8/site-packages/compliance_checker/data
WORKDIR /glider-dac
# not clear why reinstalling Mongo-related dependencies is necessary under
# Python 3, but this allows the service to run without import or runtime errors
RUN pip install -U pip && \
    pip install --no-cache Cython thredds_crawler pytest && \
    pip install --no-cache -r requirements.txt && \
    pip uninstall -y mongokit && \
    pip install --no-cache --force-reinstall mongokit-py3==0.9.1.1 && \
    pip install -U pymongo==2.8

RUN mkdir -p /data/submission /data/data/priv_erddap /data/data/pub_erddap \
             /erddapData/flag /erddapData/hardFlag berkeleydb \
             /data/catalog/priv_erddap && \
    chown -R glider:glider /glider-dac /data /usr/local/lib/python3.8/site-packages/compliance_checker/data && \
    ln -sf /glider-dac/scripts/crontab /etc/crontab
# HACK: Strip incompatible Sequence typing in ioos-qartod code for Py3.8 only.
# We should migrate ASAP to the SQLAlchemy branch to use supported versions
# of Python which don't need this workaround.
RUN sed -Ei 's/:[^:]+Sequence.*\]//' /usr/local/lib/python3.8/site-packages/ioos_qc/qartod.py
USER glider
ENV PYTHONPATH="${PYTHONPATH:-}:/glider-dac"

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
