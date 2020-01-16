FROM python:3.6-buster

RUN apt-get update && apt-get -y install libxml2-dev libudunits2-dev
RUN mkdir glider-dac && useradd glider
COPY . /glider-dac
WORKDIR glider-dac
# not clear why reinstalling Mongo-related dependencies is necessary under
# Python 3, but this allows the service to run without import or runtime errors
RUN pip install --no-cache Cython && \
    pip install --no-cache -r requirements.txt && \
    pip uninstall -y mongokit && \
    pip install --no-cache --force-reinstall mongokit-py3==0.9.1.1 && \
    pip install -U pymongo==2.8

RUN chown -R glider:glider /glider-dac/logs/
USER glider
# TODO: move logs elsewhere
VOLUME /glider-dac/logs/
ENV PYTHONPATH="${PYTHONPATH}:/glider_dac"

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
