from django.db import models
from django.contrib.postgres.fields import HStoreField

from accounts.models import User


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
