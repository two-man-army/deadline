"""
The Manager for the NewsfeedItem model, which handles creation of multiple type of NewsfeedItems
"""
from django.db.models import Manager

from accounts.models import User
from challenges.models import UserSubcategoryProficiency, Submission, Challenge
from social.constants import (
    NW_ITEM_SUBCATEGORY_BADGE_POST, NW_ITEM_SHARE_POST,
    NW_ITEM_SUBMISSION_LINK_POST, NW_ITEM_CHALLENGE_LINK_POST, NW_ITEM_CHALLENGE_COMPLETION_POST
)


class NewsfeedItemManager(Manager):
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

    def create_share_post(self, shared_item: 'NewsfeedItem', author: User):
        """
        Creates a 'share' of a NewsfeedItem or in other words, a NewsfeedItem that points to another
        """
        # TODO: Add validation for not creating a share of a share
        return self.create(author_id=author.id, type=NW_ITEM_SHARE_POST, content={'newsfeed_item_id': shared_item.id})

    def create_submission_link(self, submission: 'Submission', author: User):
        """
        Creates a 'link' NewsfeedItem type of a Submission
        """
        return self.create(author_id=author.id, type=NW_ITEM_SUBMISSION_LINK_POST,
                           content={
                               'submission_id': submission.id,
                               'submission_author_id': submission.author.id,
                               'submission_author_name': submission.author.username,
                               'submission_code_snippet': submission.code[:200],  # for now up until 200 characters, we'll see how this works
                               'submission_language_name': submission.language.name,
                               'submission_language_loc': 0  # temporary, as we do not store this anywhere
                           })

    def create_challenge_link(self, challenge: Challenge, author: User):
        """
        Creates a 'link' NewsfeedItem type of a Submission
        """
        return self.create(author_id=author.id, type=NW_ITEM_CHALLENGE_LINK_POST,
                           content={
                               'challenge_id': challenge.id,
                               'challenge_name': challenge.name,
                               'challenge_subcategory_name': challenge.category.name,
                               'challenge_difficulty': challenge.difficulty
                           })

    def create_challenge_completion_post(self, submission: Submission):
        """
        Creates a NewsfeedItem of type ChallengeCompletion
            ex: Stanislav has completed challenge Firefox with 100/100 score after 30 attempts
        """
        challenge = submission.challenge
        author: User = submission.author
        if not submission.has_solved_challenge():
            raise Exception(f'Submission has not solved the challenge!')

        return self.create(author_id=author.id, type=NW_ITEM_CHALLENGE_COMPLETION_POST,
                           content={
                               'challenge_id': challenge.id,
                               'challenge_name': challenge.name,
                               'submission_id': submission.id,
                               'challenge_score': challenge.score,
                               'attempts_count': author.fetch_unsuccessful_challenge_attempts_count(challenge)
                           })