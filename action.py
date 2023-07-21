from dataclasses import dataclass


@dataclass
class Action:
    running: bool
    new_scr: str
    update: bool 

    def __post_init__(self):
        if self.running is None:
            self.running = True
        if self.update is None:
            self.update = False


class QuitAction(Action):
    def __init__(self):
        super().__init__(False, None, False)
