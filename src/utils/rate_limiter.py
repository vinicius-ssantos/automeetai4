import time
import threading
from typing import Dict, Optional, Callable, Any

class RateLimiter:
    """
    Rate limiter using the token bucket algorithm.
    This class is thread-safe and can be used to limit the rate of API calls.
    """
    
    def __init__(self, rate: float, per: float = 1.0, burst: int = 1):
        """
        Initialize the rate limiter.
        
        Args:
            rate: The number of tokens to add per time period
            per: The time period in seconds
            burst: The maximum number of tokens that can be accumulated
        """
        self.rate = rate
        self.per = per
        self.burst = burst
        self.tokens = burst
        self.last_refill = time.time()
        self.lock = threading.RLock()
        
    def _refill(self) -> None:
        """
        Refill the token bucket based on the time elapsed since the last refill.
        """
        now = time.time()
        elapsed = now - self.last_refill
        
        # Calculate how many tokens to add
        new_tokens = elapsed * (self.rate / self.per)
        
        # Update the token count, but don't exceed the burst limit
        self.tokens = min(self.tokens + new_tokens, self.burst)
        
        # Update the last refill time
        self.last_refill = now
        
    def consume(self, tokens: int = 1, wait: bool = False) -> bool:
        """
        Consume tokens from the bucket.
        
        Args:
            tokens: The number of tokens to consume
            wait: Whether to wait for tokens to become available
            
        Returns:
            bool: True if tokens were consumed, False otherwise
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                # Enough tokens available, consume them
                self.tokens -= tokens
                return True
            elif wait:
                # Not enough tokens, calculate how long to wait
                deficit = tokens - self.tokens
                wait_time = deficit * (self.per / self.rate)
                
                # Wait for tokens to become available
                time.sleep(wait_time)
                
                # Refill and consume
                self._refill()
                self.tokens -= tokens
                return True
            else:
                # Not enough tokens and not waiting
                return False
                
    def __call__(self, func: Callable) -> Callable:
        """
        Decorator for rate-limiting a function.
        
        Args:
            func: The function to rate-limit
            
        Returns:
            Callable: The rate-limited function
        """
        def wrapper(*args, **kwargs):
            # Wait for a token to become available
            self.consume(wait=True)
            
            # Call the function
            return func(*args, **kwargs)
            
        return wrapper


class RateLimiterRegistry:
    """
    Registry for rate limiters.
    This class provides a singleton registry for rate limiters.
    """
    
    _instance = None
    _limiters: Dict[str, RateLimiter] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RateLimiterRegistry, cls).__new__(cls)
        return cls._instance
        
    def get_limiter(self, name: str, rate: Optional[float] = None, 
                   per: Optional[float] = None, burst: Optional[int] = None) -> RateLimiter:
        """
        Get a rate limiter by name, creating it if it doesn't exist.
        
        Args:
            name: The name of the rate limiter
            rate: The number of tokens to add per time period (only used if creating a new limiter)
            per: The time period in seconds (only used if creating a new limiter)
            burst: The maximum number of tokens that can be accumulated (only used if creating a new limiter)
            
        Returns:
            RateLimiter: The rate limiter
            
        Raises:
            ValueError: If the rate limiter doesn't exist and rate is not provided
        """
        if name not in self._limiters:
            if rate is None:
                raise ValueError(f"Rate limiter '{name}' does not exist and rate is not provided")
                
            self._limiters[name] = RateLimiter(
                rate=rate,
                per=per or 1.0,
                burst=burst or 1
            )
            
        return self._limiters[name]
        
    def remove_limiter(self, name: str) -> None:
        """
        Remove a rate limiter from the registry.
        
        Args:
            name: The name of the rate limiter to remove
        """
        if name in self._limiters:
            del self._limiters[name]