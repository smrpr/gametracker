import argparse
import logging
from bottle import request, ServerAdapter, Bottle, response

logger = logging.getLogger('PSAApiMock')

# Default value of input arguments
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8899

# URLs
_URLS_PREFIX = "/room_tracker"
_URL_GAMES_ROOM = _URLS_PREFIX + '/games_room'
_URL_VIDEOGAMES_ROOM = _URLS_PREFIX + "/videogames_room"
_URL_QUIET_ROOM = _URLS_PREFIX + "/quiet_room"
_URL_HEALTHCHECK = _URLS_PREFIX + "/healthcheck"

# Bottle application
_APP = Bottle()

games_room_status = False


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
def _error404():
    """
    Returns a 404 error if the wrong endpoint is accessed.
    :return: Custom message + 404 HTTP status.
    """
    return 'Sike! That\'s the wrong endpoint!'


@_APP.get(_URL_GAMES_ROOM)
def _get_room_occupancy():
    """
    """
    if games_room_status is True:
        code = ('<h1 style="color: #5e9ca0;"><span style="color: #2b2301;">Games room is </span>BUSY!</h1>'
                '<h2 style="color: #2e6c80;">&nbsp;</h2>'
                '<p>&nbsp;</p>')
    else:
        code = ('<h1 style="color: #5e9ca0;"><span style="color: #2b2301;">Games room is </span>FREE!</h1>'
                '<h2 style="color: #2e6c80;">&nbsp;</h2>'
                '<p>&nbsp;</p>')

    return code


@_APP.post(_URL_GAMES_ROOM)
def _post_room_occupancy(status):
    if status is True:
        games_room_status = True
    elif status is False:
        games_room_status = False
    else:
        raise Exception()


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
    logger.info("Serving API binded to %s:%s", host, port)
    _run_api_mock(server=server, debug=debug, reloader=reloader)


if __name__ == '__main__':
    description = "Serve room status API"
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
