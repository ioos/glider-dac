from glider_dac import app
import os

if os.environ.get('APPLICATION_SETTINGS') == 'development.py':
    app.run(host="localhost", port=3000, debug=True)
