from aiogram.fsm.state import State, StatesGroup


class PlanStates(StatesGroup):

    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_duration = State()

    waiting_for_edit_name = State()
    waiting_for_edit_price = State()
    waiting_for_edit_duration = State()