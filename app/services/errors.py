class BotServiceError(Exception):
    """Expected business rule violation."""


class ClientNotFoundError(BotServiceError):
    pass


class SlotNotFoundError(BotServiceError):
    pass


class SlotUnavailableError(BotServiceError):
    pass


class DailyLimitReachedError(BotServiceError):
    pass


class AlreadyBookedError(BotServiceError):
    pass


class AppointmentNotFoundError(BotServiceError):
    pass


class DuplicateSlotError(BotServiceError):
    pass


class PastSlotError(BotServiceError):
    pass

