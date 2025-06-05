import unittest
from src.factory import AutoMeetAIFactory
from src.services.in_memory_message_queue import InMemoryMessageQueue

class TestFactoryMessageQueue(unittest.TestCase):
    """Verifica integração da fila na factory."""

    def test_create_with_queue(self):
        factory = AutoMeetAIFactory()
        app = factory.create(use_message_queue=True, queue_workers=1)
        self.assertIsNotNone(app.message_queue)
        self.assertIsInstance(app.message_queue, InMemoryMessageQueue)
        app.parar_fila()

if __name__ == "__main__":
    unittest.main()
