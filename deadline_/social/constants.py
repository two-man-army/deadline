VALID_NEWSFEED_ITEM_TYPES = ['TEXT_POST', 'SUBCATEGORY_BADGE_POST']

# Holds the fields that must be populated on a newsfeed item type's content HStore field
NEWSFEED_ITEM_TYPE_CONTENT_FIELDS = {
    'TEXT_POST': ['content'],
    'SUBCATEGORY_BADGE_POST': ['proficiency_name', 'subcategory_name', 'subcategory_id']
}

NEWSFEED_ITEMS_PER_PAGE = 15
