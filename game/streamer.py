import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import cv2  # Faster than PIL
import numpy as np


class GameStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/stream":
            self.send_response(200)
            self.send_header(
                "Content-Type", "multipart/x-mixed-replace; boundary=frame"
            )
            self.end_headers()

            while True:
                try:
                    # 1. Get the raw array from the controller
                    raw_frame = self.server.game_controller.get_latest_frame()

                    if raw_frame is not None:
                        # 2. Convert Pygame format (WxH) to Image format (HxW)
                        # Pygame (X, Y, RGB) -> OpenCV (Y, X, BGR)
                        frame = np.transpose(raw_frame, (1, 0, 2))
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                        # 3. HIGH QUALITY RESIZE (Optional)
                        # If the game resolution is huge, you can scale it here to save bandwidth
                        # To keep full resolution, comment the next 2 lines
                        # width = 1280 # Target width
                        # frame = cv2.resize(frame, (width, int(frame.shape[0] * width/frame.shape[1])))

                        # 4. FAST ENCODING
                        # Quality 75-80 looks great and is much better than quality 30
                        result, encoded_img = cv2.imencode(
                            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
                        )

                        if result:
                            buffer = encoded_img.tobytes()
                            self.wfile.write(b"--frame\r\n")
                            self.send_header("Content-Type", "image/jpeg")
                            self.send_header("Content-Length", len(buffer))
                            self.end_headers()
                            self.wfile.write(buffer)
                            self.wfile.write(b"\r\n")

                    # Control the stream FPS (e.g., 0.03 = ~30 FPS)
                    # This won't affect the game's 60 FPS
                    time.sleep(0.03)

                except (BrokenPipeError, ConnectionResetError):
                    break
                except Exception as e:
                    print(f"Stream error: {e}")
                    time.sleep(0.1)

    def log_message(self, format, *args):
        pass


class GameStreamServer(HTTPServer):
    def __init__(self, game_controller):
        # Listen on all interfaces so other devices can see it
        super().__init__(("0.0.0.0", 8080), GameStreamHandler)
        self.game_controller = game_controller


def start_stream_server(game_controller):
    server = GameStreamServer(game_controller)
    print("Stream optimized: http://localhost:8080/stream")
    server.serve_forever()
