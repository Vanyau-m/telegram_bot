from app.database import Database
from app.models import Client
from app.repositories import ClientsRepository
from app.utils.dates import utc_now
from app.utils.validators import normalize_full_name, normalize_phone


class ClientsService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def register(self, telegram_id: int, full_name: str, phone: str) -> Client:
        valid_name = normalize_full_name(full_name)
        valid_phone = normalize_phone(phone)
        with self.database.transaction(immediate=True) as connection:
            return ClientsRepository.upsert(
                connection,
                telegram_id=telegram_id,
                full_name=valid_name,
                phone=valid_phone,
                created_at=utc_now(),
            )

    def get(self, telegram_id: int) -> Client | None:
        with self.database.transaction() as connection:
            return ClientsRepository.get(connection, telegram_id)

