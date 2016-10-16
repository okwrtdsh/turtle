import asyncio
import json
import math
import turtle

import websockets


class TurtleApp(object):
    now_position = (0, 0)

    def __init__(self, websocket, path):
        self.websocket, self.path = websocket, path
        self.screen = turtle.Screen()
        self.width, self.height = self.screen.screensize()

    @classmethod
    async def callback(cls, websocket, path):
        app = cls(websocket, path)
        while True:
            try:
                res = await websocket.recv()
                # print("res > ", res)
                app.dispatch(res)
            except websockets.exceptions.ConnectionClosed:
                break

    def reset(self):
        self.screen.clear()
        self.screen.screensize(self.width, self.height)
        self.screen.bgcolor("gray")
        self.pen = turtle.Pen()
        self.pen.shape("turtle")
        self.pen.penup()

    def get_position(self, x, y):
        return (x - self.width/2, self.height/2 - y)

    def get_degrees(self, now, next):
        return math.degrees(math.atan2(next[1] - now[1], next[0] - now[0]))

    def get_distance(self, now, next):
        dx = now[0] - next[0]
        dy = now[1] - next[1]
        return math.sqrt(dx*dx + dy*dy)

    def get_pensize(self, distance):
        tmp = int(math.sqrt(distance)) or 1
        return int(10/tmp) or 1

    def goto(self, x, y):
        next_position = self.get_position(x, y)
        degrees = self.get_degrees(self.now_position, next_position)
        distance = self.get_distance(self.now_position, next_position)
        self.pen.pensize(self.get_pensize(distance))
        self.pen.settiltangle(degrees)
        self.pen.goto(next_position)
        self.now_position = next_position

    def pendown(self, x, y):
        self.goto(x, y)
        self.pen.pendown()

    def penup(self):
        self.pen.penup()

    def dispatch(self, res):
        try:
            data = json.loads(res)
        except json.decoder.JSONDecodeError:
            return
        if not data.get("event"):
            data["event"] = "disconnected"
        return getattr(self, data["event"], "disconnected")(data)

    def disconnected(self, data):
        self.websocket.close()

    def connected(self, data):
        self.width, self.height = data["width"], data["height"]
        self.reset()

    def mousemove(self, data):
        self.goto(data["x"], data["y"])

    def mousedown(self, data):
        self.pendown(data["x"], data["y"])

    def mouseup(self, data):
        self.penup()


start_server = websockets.serve(TurtleApp.callback, '0.0.0.0', 8000)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
