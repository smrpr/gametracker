#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import argparse
import collections
import logging

from bottle import ServerAdapter, Bottle, request

logger = logging.getLogger('GameTrackerApi')

# Default value of input arguments
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8899

# URLs
_URLS_PREFIX = "/api"
_URL_POST = _URLS_PREFIX + '/post'
_URL_STATUS = _URLS_PREFIX + '/status'
_URL_HEALTHCHECK = _URLS_PREFIX + "/healthcheck"

ROOM_STATUS = collections.deque(maxlen=5)

# Bottle application
_APP = Bottle()


class StoppableWSGIRefServer(ServerAdapter):
    """Bottle server with builtin shutdown method
    Code taken from bottle.py source and added minor changes (marked below with comments)
    """
    srv = None

    def run(self, app):  # pragma: no cover
        from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
        from wsgiref.simple_server import make_server
        import socket

        class FixedHandler(WSGIRequestHandler):
            def address_string(self):  # Prevent reverse DNS lookups please.
                return self.client_address[0]

            def log_request(*args, **kw):
                if not self.quiet:
                    return WSGIRequestHandler.log_request(*args, **kw)

        handler_cls = self.options.get('handler_class', FixedHandler)
        server_cls = self.options.get('server_class', WSGIServer)

        if ':' in self.host:  # Fix wsgiref for IPv6 addresses.
            if getattr(server_cls, 'address_family') == socket.AF_INET:
                class server_cls(server_cls):
                    address_family = socket.AF_INET6

        srv = make_server(self.host, self.port, app, server_cls, handler_cls)
        self.srv = srv  # NOTE: Line added to original code
        srv.serve_forever()

    def shutdown(self):
        """Method to programatically stop serving in a neat way
        """
        # NOTE: Method added to original code
        if self.srv:
            self.srv.shutdown()


@_APP.error(404)
def _error404(error):
    """
    Returns a 404 error if the wrong endpoint is accessed.
    :return: Custom message + 404 HTTP status.
    """
    return 'Sike! That\'s the wrong endpoint!', error


@_APP.post(_URL_POST)
def _save_room_status():
    ROOM_STATUS.append(request.json)


@_APP.get(_URL_STATUS)
def _get_room_status():
    if len(ROOM_STATUS) == 0:
        return "Still haven't received any data."
    
    return ROOM_STATUS[-1]


@_APP.get(_URL_HEALTHCHECK)
def _healthcheck():
    """
    Healthcheck endpoint
    :return: 200 HTTP Response code
    """
    return "Healthy!"


def _run_api_mock(server, debug=False, reloader=False):
    """Run PSA API mock Bottle app with given Bottle server
    :param server: Bottle ServerAdapter subclass instance
    :param debug: enable debug mode if True
    :param reloader: automatically reload code changes if True
    """
    _APP.run(server=server, debug=debug, reloader=reloader)


def serve_api_mock(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=False, reloader=False):
    """Serve PSA API mock in foreground
    :param host: host address to bind to (0.0.0.0 = any)
    :param port: port to bind to
    :param debug: enable debug mode if True
    :param reloader: automatically reload code changes if True
    """
    server = StoppableWSGIRefServer(host=host, port=port)
    logger.info("Serving ECHO API mock binded to %s:%s", host, port)
    _run_api_mock(server=server, debug=debug, reloader=reloader)


if __name__ == '__main__':
    description = "Serve PSA API mock"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-p", "--port",
                        dest="port",
                        help="Server port",
                        type=int,
                        default=DEFAULT_PORT)
    parser.add_argument("-a", "--address",
                        dest="address",
                        help="Bind address",
                        default=DEFAULT_HOST)
    parser.add_argument("-r", "--reloader",
                        dest="reloader",
                        action="store_true",
                        help="Automatically reload code changes")
    parser.add_argument("-d", "--debug",
                        dest="debug",
                        action="store_true",
                        help="Debug mode")
    args = parser.parse_args()

    serve_api_mock(host=args.address, port=args.port, debug=args.debug, reloader=args.reloader)
