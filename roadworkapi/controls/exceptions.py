class RoadworkApiException(Exception):
    pass


class PublicException(RoadworkApiException):
    def __init__(self, message, response_code, error):
        super(PublicException, self).__init__(message)
        self.response_code = response_code
        self.error = error


class ConstraintException(PublicException):
    pass


class ValidationException(PublicException):
    pass
