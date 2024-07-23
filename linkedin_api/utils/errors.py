class ChallengeException(Exception):
    pass


class UnauthorizedException(Exception):
    pass


class Error(Exception):
    pass


class LinkedinSessionExpired(Error):
    pass
