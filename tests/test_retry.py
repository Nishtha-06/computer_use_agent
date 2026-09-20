# this file manually tests the RetryManager component
# of the computer Use Agent

from computer.retry import RetryManager

retry_manager = RetryManager(max_retries=3)

print("\n---Retry Test---")

for attempt in range(1,5):
    retry_allowed = retry_manager.record_failure()

    print(f"Attempt {attempt}")
    print(f"Failed attempts: {retry_manager.get_attempt_count()}")
    print(f"Retry allowed: {retry_allowed}")
    print(f"Should stop: {retry_manager.should_stop()}")
    print()