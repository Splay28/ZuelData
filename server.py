from tornado.httpserver import HTTPServer
from tornado.wsgi import WSGIContainer
from main import app
from tornado.ioloop import IOLoop
s = HTTPServer(WSGIContainer(app))
s.listen(8080)
print('run...')
IOLoop.current().start()