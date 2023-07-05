from dataclasses import dataclass


@dataclass
class Action:
    running: bool
    new_scr: str

    def __post_init__(self):
        if self.running is None:
            self.running = True


class QuitAction(Action):
    def __init__(self):
        super().__init__(False, None)
