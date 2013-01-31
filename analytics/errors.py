

class ApiError(Exception):

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return repr(self.message)
