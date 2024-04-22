import datetime
import functools
from sqlalchemy import func
from flask import current_app
import re

# Create datetime jinja2 filter
def datetimeformat(value, format='%a, %b %d %Y at %I:%M%p'):
    if isinstance(value, datetime.datetime):
        return value.strftime(format)
    return value

def timedeltaformat(starting, ending):
    if isinstance(starting, datetime.datetime) and isinstance(ending, datetime.datetime):
        return ending - starting
    return "unknown"

def prettydate(d):
    if d is None:
        return "never"
    utc_dt = datetime.datetime.utcnow()
    if utc_dt > d:
        return prettypastdate(d, utc_dt - d)
    else:
        return prettyfuturedate(d, d - utc_dt)

# from http://stackoverflow.com/a/5164027/84732
def prettypastdate(d, diff):
    s = diff.seconds
    if diff.days > 7:
        return d.strftime('%Y %b %d')
    elif diff.days > 1:
        return '{} days ago'.format(diff.days)
    elif diff.days == 1:
        return '1 day ago'
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{} seconds ago'.format(s)
    elif s < 120:
        return '1 minute ago'
    elif s < 3600:
        return '{} minutes ago'.format(s//60)
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{} hours ago'.format(s//3600)

def prettyfuturedate(d, diff):
    s = diff.seconds
    if diff.days > 7:
        return d.strftime('%Y %b %d')
    elif diff.days > 1:
        return '{} days from now'.format(diff.days)
    elif diff.days == 1:
        return '1 day from now'
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{} seconds from now'.format(s)
    elif s < 120:
        return '1 minute from now'
    elif s < 3600:
        return '{} minutes from now'.format(s/60)
    elif s < 7200:
        return '1 hour from now'
    else:
        return '{} hours from now'.format(s/3600)

def pluralize(number, singular = '', plural = 's'):
    if number == 1:
        return singular
    else:
        return plural

# TODO: move to CSS `text-overflow: ellipsis;`
# pad/truncate filter (for making text tables)
def padfit(value, size):
    if len(value) <= size:
        return value.ljust(size)

    return value[0:(size-3)] + "..."


def slugify(value):
    """
    Normalizes string, removes non-alpha characters, and converts spaces to hyphens.
    Pulled from Django
    """
    value = re.sub(r'[^\w\s-]', '', value).strip()
    return re.sub(r'[-\s]+', '-', value)


def slugify_sql(value):
    return func.regexp_replace(
            func.regexp_replace(
              func.regexp_replace(value, r'[^\w\s-]', ''), r'[-\s]+', '-'),
            r"^\s+|\s+$", "")


def get_thredds_catalog_url():
    args = {
        'host': current_app.config['THREDDS']
    }
    url = 'http://%(host)s/thredds/catalog.xml' % args
    return url


def get_erddap_catalog_url():
    args = {
        'host': current_app.config['PUBLIC_ERDDAP']
    }
    url = 'http://%(host)s/erddap/metadata/iso19115/xml/' % args
    return url


def email_exception_logging_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            current_app.logger.exception("Exception occurred while attempting to send "
                                  "email: ")
    return wrapper
