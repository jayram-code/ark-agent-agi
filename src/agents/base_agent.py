class BaseAgent:
    def __init__(self, name, orchestrator):
        self.name = name
        self.orchestrator = orchestrator

    def receive(self, message: dict):
        raise NotImplementedError("Subclasses must implement this method.")
