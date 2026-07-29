import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import Settings


class ConfigTest(unittest.TestCase):
    def test_reads_env_file_without_python_dotenv(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "BOT_TOKEN=test-token\n"
                "MASTER_TELEGRAM_ID=12345\n"
                "MAX_APPOINTMENTS_PER_DAY=8\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                settings = Settings.from_env(env_file)

        self.assertEqual(settings.bot_token, "test-token")
        self.assertEqual(settings.master_telegram_id, 12345)
        self.assertEqual(settings.max_appointments_per_day, 8)


if __name__ == "__main__":
    unittest.main()

