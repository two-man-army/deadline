# Selects the top submissions for a given challenge, always selecting the TOP scoring submission for each author
SUBMISSION_SELECT_TOP_SUBMISSIONS_FOR_CHALLENGE = ('SELECT id, author_id, max(result_score) as maxscore '
                                                   'FROM challenges_submission '
                                                   'WHERE challenge_id = %s '
                                                   'GROUP BY author_id '
                                                   'ORDER BY maxscore DESC, created_at ASC;')
# Does not pass CI
# SUBMISSION_SELECT_TOP_SUBMISSION_FOR_CHALLENGE_BY_USER = ('SELECT id, max(result_score) as maxscore '
#                                                           'FROM challenges_submission '
#                                                           'WHERE challenge_id = %s '
#                                                           'AND author_id = %s '
#                                                           'AND pending = 0')
SUBMISSION_SELECT_TOP_SUBMISSION_FOR_CHALLENGE_BY_USER = ('SELECT id, result_score as maxscore '
                                                          'FROM challenges_submission '
                                                          'WHERE challenge_id = %s AND '
                                                          'author_id = %s AND '
                                                          'pending = 0 '
                                                          'ORDER by result_score DESC '
                                                          'LIMIT 1;')

SUBMISSION_SELECT_LAST_10_SUBMISSIONS_GROUPED_BY_CHALLENGE_BY_AUTHOR = ('SELECT * '
                                                                        'FROM challenges_submission '
                                                                        'WHERE author_id = %s '
                                                                        'GROUP BY challenge_id '
                                                                        'ORDER BY created_at DESC '
                                                                        'LIMIT 10;')
