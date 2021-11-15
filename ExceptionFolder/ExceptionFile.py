class StopListeningSendMessage(Exception):
    
    def __init__(self):
        message = "STOP LISTENING START SENDING"
        self.message = message
        super().__init__(self.message)