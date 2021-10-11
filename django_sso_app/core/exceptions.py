from allauth.exceptions import ImmediateHttpResponse


class BaseException(Exception):
    def __init__(self, msg=None):
        self.msg = str(msg)


class DjangoStaffUsersCanNotLoginException(BaseException):
    pass


class AuthenticationFailed(BaseException):
    pass


class InvalidToken(BaseException):
    pass


class TokenError(BaseException):
    pass


class ProfileIncompleteException(ImmediateHttpResponse):
    pass


class DectivatedUserException(Exception):
    pass


class UnsubscribedUserException(Exception):
    pass


class ServiceSubscriptionRequiredException(ImmediateHttpResponse):
    pass


class RequestHasValidJwtWithNoDeviceAssociated(BaseException):
    pass


class UndefinedRequestUserException(BaseException):
    pass


class AnonymousUserException(BaseException):
    pass
