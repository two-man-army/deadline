MIN_SUBMISSION_INTERVAL_SECONDS = 10  # the minimum time a user must wait between submissions
MAX_TEST_RUN_SECONDS = 5  # the maximum time a Submission can run

# Keys for the object returned by the grader's AsyncResult function
GRADER_TEST_RESULTS_RESULTS_KEY = 'results'
GRADER_TEST_RESULT_SUCCESS_KEY = 'success'
GRADER_TEST_RESULT_TIME_KEY = 'time'
GRADER_TEST_RESULT_DESCRIPTION_KEY = 'description'
GRADER_TEST_RESULT_TRACEBACK_KEY = 'traceback'
GRADER_TEST_RESULT_ERROR_MESSAGE_KEY = 'error_message'
