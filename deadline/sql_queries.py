# Selects the top submissions for a given challenge, always selecting the TOP scoring submission for each author
SUBMISSION_SELECT_TOP_SUBMISSIONS_FOR_CHALLENGE = ('SELECT id, author_id, max(result_score) as maxscore '
                                                   'FROM challenges_submission '
                                                   'WHERE challenge_id = %s '
                                                   'GROUP BY author_id '
                                                   'ORDER BY maxscore DESC, created_at ASC;')