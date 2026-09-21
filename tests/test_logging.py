import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np
from fastapi import WebSocketDisconnect

from gestos import server


class Socket:
    query_params = {}

    def __init__(self, frames):
        self.frames = iter(frames)
        self.replies = []

    async def accept(self):
        pass

    async def receive_bytes(self):
        try:
            return next(self.frames)
        except StopIteration:
            raise WebSocketDisconnect()

    async def send_text(self, message):
        self.replies.append(message)


class LoggingTests(unittest.IsolatedAsyncioTestCase):
    async def test_repeated_frames_do_not_flood_logs_or_drop_replies(self):
        image = cv2.imencode('.jpg', np.zeros((32, 32, 3), dtype=np.uint8))[1].tobytes()
        socket = Socket([image] * 100)
        result = SimpleNamespace(hand_landmarks=[])
        with patch.object(server.detector, 'detect', return_value=result):
            with self.assertLogs(server.logger, level='DEBUG') as logs:
                await server.websocket_video(socket)
        self.assertEqual(len(socket.replies), 100)
        self.assertEqual([r.levelname for r in logs.records], ['INFO', 'DEBUG', 'INFO'])
        self.assertIn('NENHUMA_MAO', logs.output[1])

    async def test_bad_frames_warn_once_until_recovery(self):
        image = cv2.imencode('.jpg', np.zeros((32, 32, 3), dtype=np.uint8))[1].tobytes()
        socket = Socket([b''] * 50 + [image] + [b''] * 50)
        result = SimpleNamespace(hand_landmarks=[])
        with patch.object(server.detector, 'detect', return_value=result):
            with self.assertLogs(server.logger, level='INFO') as logs:
                await server.websocket_video(socket)
        self.assertEqual(len(socket.replies), 101)
        self.assertEqual(sum(r.levelname == 'WARNING' for r in logs.records), 2)
        self.assertEqual(sum(r.levelname == 'DEBUG' for r in logs.records), 0)


if __name__ == '__main__':
    unittest.main()
