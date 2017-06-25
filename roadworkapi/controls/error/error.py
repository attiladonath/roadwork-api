from roadworkapi.controls.error.reference import Reference


class Error():
    def __init__(self, message, code, reference=Reference()):
        self.message = message
        self.code = code
        self.reference = reference
