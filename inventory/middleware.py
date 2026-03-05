import threading

_thread_locals = threading.local()

def get_current_user():
    """
    Returns the current user from thread-local storage.
    """
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """
    Middleware to store the current user in thread-local storage.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store the user in thread-local storage
        _thread_locals.user = request.user if request.user.is_authenticated else None
        
        response = self.get_response(request)
        
        # Clean up after the request is done
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
            
        return response
