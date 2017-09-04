from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from taobaoke import app
from taobaoke.heartbeat_manager import HeartBeatManager

HeartBeatManager().run()
http_server = HTTPServer(WSGIContainer(app))
http_server.listen(49882)
IOLoop.instance().start()
