from glider_dac import app
import os

def initialize_logs(app):
    '''
    Initializes the Application Logger
    '''
    print "INITIALIZING LOGGING"
    import logging
    log_path = app.config.get('LOG_DIR', 'logs')
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    file_handler = logging.FileHandler(os.path.join(log_path, 'application.log'))
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(process)d - %(name)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Utility Application Process Started')

from flask import jsonify, url_for

def has_no_empty_params(rule):
    '''
    Something to do with empty params?
    '''
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

#@app.route('/site-map', methods=['GET'])
def site_map():
    '''
    Returns a json structure for the site routes and handlers
    '''
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint)
            links.append((url, rule.endpoint))
    # links is now a list of url, endpoint tuples
    return jsonify(rules=links)
initialize_logs(app)

if os.environ.get('APPLICATION_SETTINGS') == 'development.py':
    app.run(host="localhost", port=3000, debug=True)
