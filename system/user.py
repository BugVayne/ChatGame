class User:
    def __init__(self, name_):
        self.name = name_
        self.history = []
    
    def add_to_history(self, message):
        self.history.append(message)