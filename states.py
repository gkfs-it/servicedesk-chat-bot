from aiogram.fsm.state import State, StatesGroup


class AccessFSM(StatesGroup):
    waiting_password = State()


class TicketFSM(StatesGroup):
    waiting_login = State()
    waiting_subject = State()
    waiting_description = State()
    waiting_priority = State()
    waiting_photos = State()
    confirming = State()
