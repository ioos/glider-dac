# Debian Python image already has an ENV var called
# PYTHON_VERSION, so use a different name
# for interpolation in the FROM instruction
# and VOLUME instruction corresponding to Compliance
# Checker cache to avoid collision and using wrong
# path for volume
FROM python:3.12
ENV UDUNITS2_XML_PATH=/usr/share/xml/udunits/udunits2.xml \
  PYTHONPATH="/glider-dac" FLASK_APP=glider_dac:create_app
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/
COPY . /glider-dac

# Install system dependencies
# Install cf-units FIRST (valid version, with source fallback)
# Then install the remainder of the app requirements
RUN apt-get update && \
  apt-get -y install rsync libudunits2-dev curl && \
  uv pip install --system -r /glider-dac/requirements.txt && \
  rm -rf /var/lib/apt/lists/*

# Volume and working directories
VOLUME /glider-dac/logs/ /data /usr/local/lib/python3.12/site-packages/compliance_checker/data

WORKDIR /glider-dac

RUN mkdir -p /data/submission /data/data/priv_erddap /data/data/pub_erddap \
  /erddapData/flag /erddapData/hardFlag  \
  /data/catalog/priv_erddap

EXPOSE 5000

CMD ["gunicorn", "-k", "gevent", "-w", "4", "-b", "0.0.0.0:5000", "glider_dac:create_app()"]
