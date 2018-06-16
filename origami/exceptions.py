class OrigamiException(Exception):
    """
    Base class for all exceptions thrown by origami.
    """
    STATUS_CODE = 1

    def __init__(self, message=''):
        super().__init__("OrigamiException[{0}] => {1}".format(
            self.STATUS_CODE, message))


class MismatchTypeException(OrigamiException):
    """
    These exceptions are caused during mismatched types.
    """
    STATUS_CODE = 100


class InvalidCachePathException(OrigamiException):
    """
    Global cache path is not valid, either due to permission or is not
    a directory at all.
    """
    STATUS_CODE = 200


class MalformedCacheException(OrigamiException):
    """
    The contents of the cache files are malformed.
    """
    STATUS_CODE = 201


class BlobCreationException(OrigamiException):
    """
    Exception during creating a blob(for image) to cache into the disk
    from image_object(generally from user request files).
    """
    STATUS_CODE = 202


class InputHandlerException(OrigamiException):
    """
    Exception while handling user request input.
    """
    STATUS_CODE = 300


class OutputHandlerException(OrigamiException):
    """
    Exception while handling data for sending output to user.
    """
    STATUS_CODE = 301


class InvalidRequestParameterGet(OrigamiException):
    """
    These exceptions are caused when reqeusting invalid input parameters from
    user request.
    """
    STATUS_CODE = 302


class OrigamiRequesterException(OrigamiException):
    """
    Some other status code when requesting resource using OrigmaiRequester
    """
    STATUS_CODE = 400


class BadRequestException(OrigamiException):
    """
    400 when making a request using OrigamiRequester.
    """
    STATUS_CODE = 401


class NotFoundRequestException(OrigamiException):
    """
    404 when requesting a resource using OrigamiRequester
    """
    STATUS_CODE = 402


class InternalServerErrorException(OrigamiException):
    """
    500 when requesting the resource using OrigamiRequester
    """
    STATUS_CODE = 403


class InvalidTokenException(OrigamiException):
    """
    These exceptions are caused by providing invalid token to origami
    while registering app.
    """
    STATUS_CODE = 500


class InavalidMimeTypeException(OrigamiException):
    """
    The mime type provided for image is not valid
    """
    STATUS_CODE = 501


class InvalidFilePathException(OrigamiException):
    """
    File not found for the path provided
    """
    STATUS_CODE = 502


class OrigamiServerException(OrigamiException):
    """
    These exceptions are caused during error during server running.
    """
    STATUS_CODE = 503


class FileHandlingException(OrigamiException):
    """
    Genric exception when error during handling file
    (create, update, read, delete)
    """
    STATUS_CODE = 504
