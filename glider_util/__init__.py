# Create datetime jinja2 filter
def datetimeformat(value, format='%a, %b %d %Y at %I:%M%p'):
    if isinstance(value, datetime.datetime):
        return value.strftime(format)
    return value
