import unittest
import time

from src.services.in_memory_message_queue import InMemoryMessageQueue


class TestInMemoryMessageQueue(unittest.TestCase):
    """Testes para a fila de mensagens em memória."""

    def test_processamento_assincrono(self):
        resultados = []

        def handler(msg):
            resultados.append(msg)

        fila = InMemoryMessageQueue(handler)
        fila.iniciar(num_workers=1)

        fila.publicar("teste1")
        fila.publicar("teste2")

        time.sleep(0.2)
        fila.parar()

        self.assertEqual(resultados, ["teste1", "teste2"])


if __name__ == "__main__":
    unittest.main()
