import inspect
import logging
from functools import wraps


def retry(enable_retry_keyword='enable_retry',
          retry_limit_keyword='retry_limit',
          on_retry_prepare_method_name_in_class=None,
          on_retry_prepare=None,
          validate_retryable_response=None,
          validate_retryable_response_method_name_in_class=None,
          verbose=False,
          verbose_param_name='verbose_on_retry'):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt_count = 0
            response = None

            # Retrieve the function signature and bind the provided arguments
            final_arguments = inspect.signature(
                func).bind_partial(*args, **kwargs)

            # Apply the default values
            final_arguments.apply_defaults()

            # Check if the retry is enabled
            enable_retry = final_arguments.arguments.get(
                enable_retry_keyword, False)

            # Retrieve retry limit
            retry_limit = final_arguments.arguments.get(retry_limit_keyword, 0)

            # Retrieve verbose
            final_verbose = final_arguments.arguments.get(
                verbose_param_name, verbose)

            # Get the class self instance
            self = final_arguments.arguments['self'] if final_arguments.arguments.get(
                'self', None) else None

            # Get the retry preparation method
            if on_retry_prepare:
                final_on_retry_prepare = on_retry_prepare
            else:
                final_on_retry_prepare = getattr(self, on_retry_prepare_method_name_in_class,
                                                 None) if on_retry_prepare_method_name_in_class else None

            # Get the validate retryable response method
            if validate_retryable_response:
                final_validate_retryable_response = validate_retryable_response
            else:
                final_validate_retryable_response = getattr(self, validate_retryable_response_method_name_in_class,
                                                            None) if validate_retryable_response_method_name_in_class else None

            if final_verbose:
                config = {
                    'enable_retry': enable_retry,
                    'retry_limit': retry_limit,
                    'verbose': final_verbose,
                    'enable_final_on_retry_prepare': bool(final_on_retry_prepare),
                    'enable_validate_retryable_response': bool(final_validate_retryable_response),
                }
                logging.debug(f"Final configuration: {config}")

            while attempt_count <= retry_limit:
                attempt_count += 1

                if final_verbose:
                    logging.debug(f"Current attempt: {attempt_count}")

                # Get the response
                response = func(*args, **kwargs)

                # Check if the response is retryable
                response_is_retryable = final_validate_retryable_response(
                    response) if callable(final_validate_retryable_response) else False

                # If the response is retryable, retry is enabled, and current attempt count is under retry limit, then retry
                if response_is_retryable and enable_retry and attempt_count <= retry_limit:
                    if final_verbose:
                        logging.debug(
                            f"Retrying since its response is retryable, retry is enabled, and attempt count {attempt_count} is under or equal to retry limit {retry_limit}")

                    if callable(final_on_retry_prepare):
                        if final_verbose:
                            logging.debug(
                                f"Triggering retry preparation method")

                        final_on_retry_prepare()

                # Otherwise, break the loop
                else:
                    if final_verbose:
                        if not response_is_retryable:
                            logging.debug(
                                f"Stopped retrying since the response is not retryable")
                        elif not enable_retry:
                            logging.debug(
                                f"Stopped retrying since retry is not enabled")
                        elif attempt_count > retry_limit:
                            logging.debug(
                                f"Stopped retrying since attemp count {attempt_count} exceeds the retry limit {retry_limit}")

                    break

            return response
        return wrapper
    return decorator
