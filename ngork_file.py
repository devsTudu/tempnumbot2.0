from http.server import HTTPServer
import ngrok

from app import app

server = HTTPServer(("localhost",5000),app)
ngrok.listen(server)
ngrok.serve_forever()
