# this file provides provides retry and failure handling logic for the
# computer use agent.
# It tracks consecutive unsuccessful attempts and decides
# whether the agent should retry or stop.

class RetryManager:
    """Manage consecutive failed attempts."""

    def __init__(self,max_retries = 3):
        """Initializee the retry manager."""
        self.max_retries = max_retries
        self.failed_attempts = 0

    def reset(self):
        """Reset the failed attempt counter."""
        self.failed_attempts = 0

    def record_failure(self):
        """Record one failed attempt and return whether retry is allowed."""
        self.failed_attempts += 1
        return self.failed_attempts < self.max_retries

    def should_stop(self):
        """Return True when the retry limit has been reached."""
        return self.failed_attempts >= self.max_retries

    def get_attempt_count(self):
        """Return the current number of failed attempts."""
        return self.failed_attempts