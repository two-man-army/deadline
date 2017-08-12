NW_ITEM_TEXT_POST = 'TEXT_POST'
NW_ITEM_SUBCATEGORY_BADGE_POST = 'SUBCATEGORY_BADGE_POST'

VALID_NEWSFEED_ITEM_TYPES = [NW_ITEM_TEXT_POST, NW_ITEM_SUBCATEGORY_BADGE_POST]

# Holds the fields that must be populated on a newsfeed item type's content HStore field
NEWSFEED_ITEM_TYPE_CONTENT_FIELDS = {
    NW_ITEM_TEXT_POST: ['content'],
    NW_ITEM_SUBCATEGORY_BADGE_POST: ['proficiency_name', 'subcategory_name', 'subcategory_id']
}

NEWSFEED_ITEMS_PER_PAGE = 15
