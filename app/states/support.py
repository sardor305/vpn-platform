from aiogram.fsm.state import State, StatesGroup


class SupportStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_admin_reply = State()
    waiting_for_user_reply = State()