FROM python:3.11
ENV PYTHONPATH="/glider-dac" FLASK_APP=glider_dac:create_app
COPY . /glider-dac

# Install system dependencies
# Install cf-units FIRST (valid version, with source fallback)
# Then install the remainder of the app requirements
RUN apt-get update && \
    apt-get -y install rsync && \
    pip install --no-cache -U pip && \
    pip install --no-cache -r /glider-dac/requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Volume and working directories
VOLUME /glider-dac/logs/ /data /usr/local/lib/python3.11/site-packages/compliance_checker/data

WORKDIR /glider-dac

RUN mkdir -p /data/submission /data/data/priv_erddap /data/data/pub_erddap \
             /erddapData/flag /erddapData/hardFlag  \
             /data/catalog/priv_erddap

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "glider_dac:create_app()"]
