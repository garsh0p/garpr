activate_this = '/drive1/Code/smash-ranks-stable/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from server import app as application
import sys
sys.path.insert(0, '/work/smash-ranks-stable')
