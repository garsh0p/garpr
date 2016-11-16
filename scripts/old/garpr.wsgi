activate_this = '/work/garpr/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/work/garpr')

from server import app as application
