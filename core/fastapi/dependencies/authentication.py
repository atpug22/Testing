from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.exceptions.base import CustomException


class AuthenticationRequiredException(CustomException):
    code = status.HTTP_401_UNAUTHORIZED
    error_code = status.HTTP_401_UNAUTHORIZED
    message = "Authentication required"


class AuthenticationRequired:
    def __init__(
        self,
        request: Request,
        token: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    ):
        # Check if user is already authenticated by middleware
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'id') and request.user.id:
            return  # User is already authenticated
        
        # Fall back to Bearer token if no session
        if not token:
            raise AuthenticationRequiredException()
