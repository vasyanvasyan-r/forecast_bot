from aiogram.fsm.state import StatesGroup, State

class AuthStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_password = State()

class ForecastStates(StatesGroup):
    roma_score_fh = State()
    rival_score_fh = State()
    roma_score_ft = State()
    rival_score_ft = State()

    entering_scorers = State()
    entering_assists = State()
    entering_first_goal = State()
    
