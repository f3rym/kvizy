from aiogram.fsm.state import State, StatesGroup


class FileStates(StatesGroup):
    """FSM states for file operations"""

    # Creating file
    waiting_for_file_content = State()

    # Editing file
    waiting_for_new_content = State()

    # Confirmation
    waiting_for_confirmation = State()
