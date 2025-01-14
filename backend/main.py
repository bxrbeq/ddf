import os
import json
import asyncio
import mimetypes
from http.server import SimpleHTTPRequestHandler, HTTPServer
import http.client
from urllib.parse import urlparse
from urllib.parse import unquote
import websockets
import ssl
from collections import defaultdict
from http.cookies import SimpleCookie

portHTTP = 8080
portWS = 9090

class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Existing GET logic (serving files) remains here
        path = self.path.split('?')[0]
        print(path)

        match path.lower():
            case '/': #home
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                with open('C:\\Users\\Leon\\Documents\\00\\coding\\3_übergreifende-projekte\\ddf\\test.html', 'rb') as file:
                    self.wfile.write(file.read())
            case '/login': #login via twitch
                self.send_response(200)
            case s if '/media' in s: #media files
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
                self.wfile.write(b'Der Holzweg... :/')


class WebsocketHandler():

    game_connections = defaultdict(set)

    async def websocket_handler(websocket, path):
        game_connections = WebsocketHandler.game_connections
        #vaildate game
        game_valid: bool = False
        if path.startswith("/game/"):
            gameID = path[len("/game/"):]
            open_games = open('folder.txt').read()
            if gameID in open_games:
                game_valid = True

        #validate user
        headers = websockets.request_headers
        cookies_header = headers.get('Cookie', '')
        cookie = SimpleCookie(cookies_header)
        parsed_cookies = {key: morsel.value for key, morsel in cookie.items()}
        auth = parsed_cookies.get('auth')
        userID = parsed_cookies.get('userID')
        
        login_valid = await twitch.validateUser(userID, auth)

        if game_valid and login_valid:
            #add user to active connections
            game_connections[gameID].add(websocket)

            try:
                async for message in websocket:
                    await WebsocketHandler.send_messages(gameID, f"Broadcast: {message}")
            except websockets.ConnectionClosed:
                print(f"Connection closed for game {gameID}")
            finally:
                game_connections[gameID].remove(websocket)
                if not game_connections[gameID]:
                    del game_connections[gameID]


    async def send_messages(gameID, msg):
        game_connections = WebsocketHandler.game_connections
        if gameID in game_connections:
            for websocket in game_connections[gameID]:
                if websocket.open:
                    try:
                        await websocket.send(msg)
                    except websockets.ConnectionClosed:
                        print(f"Failed to send message to a client in game {gameID}")


class twitch():
    async def validateUser(id, auth):
        conn = http.client.HTTPSConnection('api.twitch.tv')
        headers = {
            'Authorization': f'Bearer {auth}',
            'Client-Id': '',        # wichtig
        }
        conn.request('GET', f'/helix/users?id={id}', headers=headers)
        response = conn.getresponse()
        if response.status() == 200:
            return True

# start http server
def start_http_server():
    server_address = ('', portHTTP)
    http_server = HTTPServer(server_address, RequestHandler)
    print(f'HTTP Server is running on port {portHTTP}...')
    http_server.serve_forever()
# start ws server 
async def start_websocket_server():
    server = await websockets.serve(
        WebsocketHandler.websocket_handler,
        '',
        port=portWS,
        ssl=None    # ssl certificate here later 
    )
    print(f"WebSocket server is running on port {portWS}...")
    await server.wait_closed()


if __name__ == "__main__":
    # Run HTTP server in the background
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, start_http_server)
    
    # Run WebSocket server
    asyncio.run(start_websocket_server())