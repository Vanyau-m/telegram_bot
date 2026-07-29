from telegram import ReplyKeyboardMarkup


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["Готово"], ["/cancel"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )

