import sys
import os

# Set up paths for HostAfrica / cPanel Passenger WSGI
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application
