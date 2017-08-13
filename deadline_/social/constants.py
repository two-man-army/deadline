NW_ITEM_TEXT_POST = 'TEXT_POST'
NW_ITEM_SUBCATEGORY_BADGE_POST = 'SUBCATEGORY_BADGE_POST'
NW_ITEM_SHARE_POST = 'SHARE_POST'
NW_ITEM_SUBMISSION_LINK_POST = 'SUBMISSION_LINK_POST'

VALID_NEWSFEED_ITEM_TYPES = [NW_ITEM_TEXT_POST, NW_ITEM_SUBCATEGORY_BADGE_POST, NW_ITEM_SHARE_POST, NW_ITEM_SUBMISSION_LINK_POST]

# Holds the fields that must be populated on a newsfeed item type's content HStore field
NEWSFEED_ITEM_TYPE_CONTENT_FIELDS = {
    NW_ITEM_TEXT_POST: ['content'],
    NW_ITEM_SUBCATEGORY_BADGE_POST: ['proficiency_name', 'subcategory_name', 'subcategory_id'],
    NW_ITEM_SHARE_POST: ['newsfeed_item_id'],
    NW_ITEM_SUBMISSION_LINK_POST: ['submission_id', 'submission_author_name', 'submission_author_id',
                                   'submission_code_snippet', 'submission_language_name', 'submission_language_loc']
}

NEWSFEED_ITEMS_PER_PAGE = 15
