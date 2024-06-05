class SubmissionMissingException(BaseException):
    pass


class Checker:
    def __init__(self):
        raise NotImplementedError

    def check(self):
        raise NotImplementedError
