# Debian Python image already has an ENV var called
# PYTHON_VESION, so use a different name
# for interpolation in the FROM instruction
# and VOLUME instruction corresponding to Compliance
# Checker cache to avoid collision and using wrong
# path for volume
ARG PYTHON_VERSION_SHORT=3.11
FROM python:$PYTHON_VERSION_SHORT
ENV UDUNITS2_XML_PATH=/usr/share/xml/udunits/udunits2.xml \
    PYTHONPATH="/glider-dac" FLASK_APP=glider_dac:create_app
ARG PYTHON_VERSION_SHORT=3.11
COPY . /glider-dac



# Install system dependencies
# Install cf-units FIRST (valid version, with source fallback)
# Then install the remainder of the app requirements
RUN apt-get update && \
    apt-get -y install rsync libudunits2-dev && \
    pip install --no-cache -U pip && \
    pip install --no-cache -r /glider-dac/requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Volume and working directories
VOLUME /glider-dac/logs/ /data /usr/local/lib/python$PYTHON_VERSION_SHORT/site-packages/compliance_checker/data

WORKDIR /glider-dac

RUN mkdir -p /data/submission /data/data/priv_erddap /data/data/pub_erddap \
             /erddapData/flag /erddapData/hardFlag  \
             /data/catalog/priv_erddap

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "glider_dac:create_app()"]
