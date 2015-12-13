#!/usr/bin/python3
from flipflop import WSGIServer
from server import app
#import newrelic.agent
#newrelic.agent.initialize('/etc/newrelic.ini')

if __name__ == '__main__':
    WSGIServer(app).run()
