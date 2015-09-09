#!/usr/bin/python3
from flipflop import WSGIServer
from server import app


if __name__ == '__main__':
    WSGIServer(app).run()
