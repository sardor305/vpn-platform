from aiogram.fsm.state import State, StatesGroup


class DailySubscriptionStates(StatesGroup):

    waiting_for_days = State()