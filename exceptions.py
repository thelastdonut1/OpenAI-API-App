# This file contains some custom exceptions used in the chat application.


class ChatError(Exception):
    '''
    Base class for exceptions raised when communicating with the API.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ModelNotFound(Exception):
    '''
    Raised when a model can not be identified in the models.json file.
    '''
    def __init__(self, message):
        super().__init__(message)
        self.message = message