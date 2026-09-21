import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np
from fastapi import WebSocketDisconnect

from gestos import server
from test_recognition import hand


class Socket:
    def __init__(self, count, rich=True):
        self.query_params = {'landmarks': '1'} if rich else {}
        self.remaining = count
        self.messages = []
        self.frame = cv2.imencode('.jpg', np.zeros((32, 32, 3), dtype=np.uint8))[1].tobytes()

    async def accept(self):
        pass

    async def receive_bytes(self):
        if not self.remaining:
            raise WebSocketDisconnect()
        self.remaining -= 1
        return self.frame

    async def send_json(self, value):
        self.messages.append(value)

    async def send_text(self, value):
        self.messages.append(value)


class GestureSocketTests(unittest.IsolatedAsyncioTestCase):
    async def test_json_reports_all_gestures_and_landmarks(self):
        poses = [hand(1,1,1,1,1), hand(0,0,0,0,1), hand(1,0,0,0,0),
                 hand(0,1,1,0,0), hand(), hand(0,1,0,0,1)]
        results = [SimpleNamespace(hand_landmarks=[pose]) for pose in poses]
        socket = Socket(len(poses))
        with patch.object(server.detector, 'detect', side_effect=results):
            await server.websocket_video(socket)
        self.assertEqual([m['command'] for m in socket.messages],
                         ['FRENTE', 'DIREITA', 'ESQUERDA', 'RE', 'PARAR', 'TROCAR_MODO'])
        self.assertTrue(all(len(m['landmarks']) == 21 for m in socket.messages))
        self.assertTrue(all(m['mode'] == 'GESTOS' for m in socket.messages))

    async def test_mode_event_once_and_new_connection_starts_in_gestures(self):
        result = SimpleNamespace(hand_landmarks=[hand(0,1,0,0,1)])
        for rich in [True, False]:
            socket = Socket(21, rich)
            with patch.object(server.detector, 'detect', return_value=result):
                with patch('gestos.modes.monotonic', side_effect=[i / 10 for i in range(21)]):
                    await server.websocket_video(socket)
            if rich:
                self.assertEqual(sum(m['mode_changed'] for m in socket.messages), 1)
                self.assertEqual(socket.messages[0]['mode'], 'GESTOS')
                self.assertEqual(socket.messages[-1]['mode'], 'AUTO')
            else:
                self.assertEqual(socket.messages.count('MODO_AUTO'), 1)
                self.assertEqual(socket.messages.count('AGUARDANDO'), 20)
