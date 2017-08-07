# Selects the top submissions for a given challenge, always selecting the TOP scoring submission for each author
SUBMISSION_SELECT_TOP_SUBMISSIONS_FOR_CHALLENGE = (
    'SELECT id, author_id, result_score '
    'FROM ('
        'SELECT id, author_id, result_score, created_at, '
        'rank() OVER (PARTITION BY author_id ORDER BY result_score DESC, created_at ASC) AS rank '
        'FROM challenges_submission '
        'WHERE challenge_id = %s) as sub '
    'WHERE sub.rank = 1 '
    'ORDER BY result_score DESC, created_at ASC'
)

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
                                                          'pending = FALSE '
                                                          'ORDER by result_score DESC '
                                                          'LIMIT 1;')

SUBMISSION_SELECT_LAST_10_SUBMISSIONS_GROUPED_BY_CHALLENGE_BY_AUTHOR = (
    'SELECT * '
    'FROM ('
        'SELECT *, rank() OVER (PARTITION BY challenge_id ORDER BY created_at DESC) as rank '
        'FROM challenges_submission '
        'WHERE author_id = %s) as sub '
    'WHERE sub.rank = 1 '
    'ORDER BY created_at DESC '
    'LIMIT 10;')
