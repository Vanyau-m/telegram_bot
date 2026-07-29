import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.services.dialog_logs import DialogLogService


class DialogLogServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_directory.name) / "test.db")
        self.database.initialize()
        self.dialog_logs = DialogLogService(self.database)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_stores_incoming_and_outgoing_messages(self):
        self.dialog_logs.log(
            direction="incoming",
            telegram_user_id=123,
            chat_id=123,
            username="test_user",
            first_name="Иван",
            message_text="Привет",
            message_type="text",
            telegram_message_id=10,
            update_id=100,
        )
        self.dialog_logs.log(
            direction="outgoing",
            telegram_user_id=123,
            chat_id=123,
            message_text="Здравствуйте!",
            message_type="text",
            telegram_message_id=11,
        )

        messages = self.dialog_logs.list_for_user(123)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].direction, "incoming")
        self.assertEqual(messages[0].message_text, "Привет")
        self.assertEqual(messages[0].username, "test_user")
        self.assertEqual(messages[1].direction, "outgoing")
        self.assertEqual(messages[1].message_text, "Здравствуйте!")


if __name__ == "__main__":
    unittest.main()

