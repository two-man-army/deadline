NW_ITEM_TEXT_POST = 'TEXT_POST'
NW_ITEM_SUBCATEGORY_BADGE_POST = 'SUBCATEGORY_BADGE_POST'
NW_ITEM_SHARE_POST = 'SHARE_POST'
NW_ITEM_SUBMISSION_LINK_POST = 'SUBMISSION_LINK_POST'
NW_ITEM_CHALLENGE_LINK_POST = 'CHALLENGE_LINK_POST'
NW_ITEM_CHALLENGE_COMPLETION_POST = 'CHALLENGE_COMPLETION_POST'

VALID_NEWSFEED_ITEM_TYPES = [NW_ITEM_TEXT_POST, NW_ITEM_SUBCATEGORY_BADGE_POST, NW_ITEM_SHARE_POST,
                             NW_ITEM_SUBMISSION_LINK_POST, NW_ITEM_CHALLENGE_LINK_POST, NW_ITEM_CHALLENGE_COMPLETION_POST]

# Holds the fields that must be populated on a newsfeed item type's content HStore field
NEWSFEED_ITEM_TYPE_CONTENT_FIELDS = {
    NW_ITEM_TEXT_POST: ['content'],
    NW_ITEM_SUBCATEGORY_BADGE_POST: ['proficiency_name', 'subcategory_name', 'subcategory_id'],
    NW_ITEM_SHARE_POST: ['newsfeed_item_id'],
    NW_ITEM_SUBMISSION_LINK_POST: ['submission_id', 'submission_author_name', 'submission_author_id',
                                   'submission_code_snippet', 'submission_language_name', 'submission_language_loc'],
    NW_ITEM_CHALLENGE_LINK_POST: ['challenge_id', 'challenge_name', 'challenge_subcategory_name', 'challenge_difficulty'],
    NW_ITEM_CHALLENGE_COMPLETION_POST: ['challenge_id', 'challenge_name', 'submission_id', 'challenge_score', 'attempts_count']
}

NEWSFEED_ITEMS_PER_PAGE = 15

# the maximum time that can pass before a submission is deemed invalid for a CHALLENGE_COMPLETION post
MAX_CHALLENGE_COMPLETION_SUBMISSION_EXPIRY_MINUTES = 10


# Notification types
RECEIVE_FOLLOW_NOTIFICATION = 'RECEIVE_FOLLOW_NOTIFICATION'
RECEIVE_FOLLOW_NOTIFICATION_SQUASHED = 'RECEIVE_FOLLOW_NOTIFICATION_SQUASHED'
NEW_CHALLENGE_NOTIFICATION = 'NEW_CHALLENGE_NOTIFICATION'

RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION = 'RECEIVE_SUBMISSION_LIKE_NOTIFICATION'
RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED = 'RECEIVE_SUBMISSION_LIKE_NOTIFICATION_SQUASHED'
RECEIVE_SUBMISSION_COMMENT_NOTIFICATION = 'RECEIVE_SUBMISSION_COMMENT_NOTIFICATION'
RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION = 'RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION'

RECEIVE_NW_ITEM_LIKE_NOTIFICATION = 'RECEIVE_NW_LIKE_NOTIFICATION'
RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED = 'RECEIVE_NW_LIKE_NOTIFICATION_SQUASHED'
RECEIVE_NW_ITEM_COMMENT_NOTIFICATION = 'RECEIVE_NW_COMMENT_NOTIFICATION'
RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED = 'RECEIVE_NW_COMMENT_NOTIFICATION_SQUASHED'
RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION = 'RECEIVE_NW_COMMENT_REPLY_NOTIFICATION'
RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED = 'RECEIVE_NW_COMMENT_REPLY_NOTIFICATION_SQUASHED'

RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION = 'RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION'
RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED = 'RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED'

VALID_NOTIFICATION_TYPES = [RECEIVE_FOLLOW_NOTIFICATION, RECEIVE_FOLLOW_NOTIFICATION_SQUASHED,
                            RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED,
                            RECEIVE_NW_ITEM_LIKE_NOTIFICATION, RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED,
                            NEW_CHALLENGE_NOTIFICATION,
                            RECEIVE_NW_ITEM_COMMENT_NOTIFICATION, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED,
                            RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED,
                            RECEIVE_SUBMISSION_COMMENT_NOTIFICATION, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION,
                            RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED]
# Holds the fields that must be populated on a notification type's content HStore field
NOTIFICATION_TYPE_CONTENT_FIELDS = {
    RECEIVE_FOLLOW_NOTIFICATION: ['follower_id', 'follower_name'],
    RECEIVE_FOLLOW_NOTIFICATION_SQUASHED: ['followers'],
    RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION: ['submission_id', 'challenge_id', 'challenge_name', 'liker_id', 'liker_name'],
    RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED: ['submission_id', 'challenge_id', 'challenge_name', 'likers'],
    RECEIVE_NW_ITEM_LIKE_NOTIFICATION: ['liker_id', 'liker_name', 'nw_type', 'nw_content', 'nw_item_id'],
    RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED: ['likers', 'nw_type', 'nw_content', 'nw_item_id'],
    NEW_CHALLENGE_NOTIFICATION: ['challenge_name', 'challenge_id', 'challenge_subcategory_name'],
    RECEIVE_NW_ITEM_COMMENT_NOTIFICATION: ['nw_item_id', 'nw_item_type', 'nw_item_content',
                                           'commenter_id', 'commenter_name'],
    RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED: ['nw_item_id', 'nw_item_type', 'nw_item_content',
                                                    'commenters'],
    RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION: ['nw_comment_id', 'replier_id', 'replier_name', 'reply_content'],
    RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED: ['nw_comment_id', 'repliers'],
    RECEIVE_SUBMISSION_COMMENT_NOTIFICATION: ['submission_id', 'challenge_id', 'challenge_name', 'commenter_name',
                                              'comment_content', 'commenter_id', 'comment_id'],
    RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION: ['submission_id', 'challenge_id', 'challenge_name', 'commenter_name',
                                                    'comment_content', 'commenter_id', 'comment_id'],
    RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION: ['challenge_id', 'challenge_name', 'replier_name',
                                                   'comment_id',
                                                   'reply_content', 'replier_id', 'reply_id'],
    RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED: ['challenge_id', 'challenge_name',
                                                            'comment_id', 'repliers']
}
