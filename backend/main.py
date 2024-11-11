import os
import json
import asyncio
import mimetypes
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from urllib.parse import unquote
from websockets import serve

portHTTP = 8080
portWS = 9090

class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Existing GET logic (serving files) remains here
        url = self.path.split('?')[0]
        path = unquote(url.strip('/'))
        print(url)
        print(path)

        match path.lower():
            case '': #home
                self.send_response(200)
            case 'login': #login via twitch
                self.send_response(200)
            case 'user': #joined as a user
                self.send_response(200)
            case 'admin': #created as admin
                self.send_response(200)
            case 'open-rounds': #return open rounds via json
                self.send_response(200)
            case s if 'media/' in s: #media files
                self.send_response(200)
                file_path = os.path.join(os.getcwd(), path)

                if os.path.exists(file_path) and os.path.isfile(file_path):
                    self.send_response(200)

                    mime_type, _ = mimetypes.guess_type(file_path)
                    self.send_header('Content-type', mime_type or 'application/octet-stream')
                    self.end_headers()

                    with open(file_path, 'rb') as file:
                        self.wfile.write(file.read())
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'File not found')
            case _: #404
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'File not found')

# start http server
def start_http_server():
    server_address = ('', portHTTP)
    http_server = HTTPServer(server_address, RequestHandler)
    print(f'HTTP Server is running on port {portHTTP}...')
    http_server.serve_forever()

async def websocket_handler(websocket):
    try:
        connection = await websocket.recv()
        print(f'New connection: {connection}')
        # verify login with twitch api
        # put in selected round
        await websocket.send('{"success": true}')

        await websocket.close()
    finally:
        print(f'user "{user} disconnected"')

# start ws server 

async def start_websocket_server():
    async with serve(websocket_handler, '', portWS):
        print(f"WebSocket Server is running on port {portWS}...")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    # Run HTTP server in the background
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, start_http_server)
    
    # Run WebSocket server
    #loop.run_until_complete(start_websocket_server())