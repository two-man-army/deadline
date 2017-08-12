from django.db import models
from django.contrib.postgres.fields import HStoreField
from django.db.models.signals import pre_save
from django.dispatch import receiver

from accounts.models import User
from challenges.models import SubCategory, UserSubcategoryProficiency
from social.constants import NEWSFEED_ITEM_TYPE_CONTENT_FIELDS, VALID_NEWSFEED_ITEM_TYPES, \
    NW_ITEM_SUBCATEGORY_BADGE_POST
from social.errors import InvalidNewsfeedItemType, MissingNewsfeedItemContentField, InvalidNewsfeedItemContentField, \
    LikeAlreadyExistsError, NonExistentLikeError


class NewsfeedItemManager(models.Manager):
    """
    Use a custom NewsfeedItem manager for specific type of NewsfeedItem creation
    """

    def create_subcategory_badge_post(self, user_subcat_prof: UserSubcategoryProficiency):
        """
        Creates a SubcategoryBadgePost

        A SubcategoryBadgePost is a NewsfeedItem which has the following fields as content:
            proficiency_name: - the name of the proficiency (or badge) the user has attained
            subcategory_name: - the name of the subcategory this badge is for
            subcategory_id:   - the id of the subcategory

        ex: Stanislav just earned the Master badge for Graph Algorithms!
        """
        return self.create(author_id=user_subcat_prof.user_id, type=NW_ITEM_SUBCATEGORY_BADGE_POST,
                           content={
                               'proficiency_name': user_subcat_prof.proficiency.name,
                               'subcategory_name': user_subcat_prof.subcategory.name,
                               'subcategory_id': user_subcat_prof.subcategory.id
                           })


class NewsfeedItem(models.Model):
    """
    NewsfeedItem is a model that holds a single item in the facebook-esque NewsFeed (or Activity Feed)
        of the website.
    Since the content here is dynamic (you can share a submission, display you've complete a challenge, etc),
        we need an HStore field to store data related to the type of the post.
    e.g
    {
        type: "completed_challenge"
        content: {
            "challenge_id": 1,
            "submission_id": 1
        }
    },
    {
        type: "created_course"
        content: {
            "course_id": 1
        }
    }
    """
    author = models.ForeignKey(User)
    type = models.CharField(max_length=30)  # no other table for now
    content = HStoreField()  # varied, depending on the type
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NewsfeedItemManager()

    def get_absolute_url(self):
        return f'/social/feed/items/{self.id}'

    def like(self, user: User):
        if NewsfeedItemLike.objects.filter(newsfeed_item=self, author=user).exists():
            raise LikeAlreadyExistsError(f'The Like from User {user.id} for Item {self.id} does already exists!')

        return NewsfeedItemLike.objects.create(author=user, newsfeed_item=self)

    def remove_like(self, user: User):
        like = NewsfeedItemLike.objects.filter(newsfeed_item=self, author=user).first()
        if like is None:
            raise NonExistentLikeError(f'The Like from User {user.id} for Item {self.id} does not exist!')

        like.delete()


@receiver(pre_save, sender=NewsfeedItem)
def nw_item_validation(sender, instance, *args, **kwargs):
    # Validate that the type is valid and contains what we expect exactly
    if instance.type not in VALID_NEWSFEED_ITEM_TYPES:
        raise InvalidNewsfeedItemType(f'{instance.type} is not a valid NewsfeedItem type!')

    # Assert that each field is present
    required_fields = NEWSFEED_ITEM_TYPE_CONTENT_FIELDS[instance.type]
    for field in required_fields:
        if field not in instance.content:
            raise MissingNewsfeedItemContentField(
                f'The field {field} must be in the content of NewsfeedItem of type {instance.type}.')

    # Assert that no other unnecessary fields are present
    if len(required_fields) < len(instance.content.keys()):
        # Some unnecessary field is present
        for field in instance.content.keys():
            if field not in required_fields:
                raise InvalidNewsfeedItemContentField(
                    f'The field {field} is not part of the expected content for {instance.type} and is unnecessary!')


class NewsfeedItemComment(models.Model):
    newsfeed_item = models.ForeignKey(NewsfeedItem, related_name='comments')
    author = models.ForeignKey(User)
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', null=True, related_name='replies', default=None)

    def add_reply(self, author, content):
        return NewsfeedItemComment.objects.create(newsfeed_item=self.newsfeed_item, parent=self, author=author, content=content)


class NewsfeedItemLike(models.Model):
    newsfeed_item = models.ForeignKey(NewsfeedItem, related_name='likes')
    author = models.ForeignKey(User)
    unique_together = ('newsfeed_item', 'author')
