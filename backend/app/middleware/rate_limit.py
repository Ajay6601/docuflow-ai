from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.config import settings

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"],  # Default rate limit
    storage_uri=settings.REDIS_URL,
)

# Custom key function to use user ID if authenticated
def get_user_id(request: Request) -> str:
    """Get user ID from request for rate limiting."""
    # Try to get user from token
    try:
        from app.dependencies import get_current_user
        from fastapi import Depends
        
        # If authenticated, use user ID
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Extract user info from token would go here
            # For now, use IP address
            pass
    except:
        pass
    
    # Fallback to IP address
    return get_remote_address(request)