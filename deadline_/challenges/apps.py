from django.apps import AppConfig


class ChallengesConfig(AppConfig):
    name = 'challenges'
    verbose_name = "Challenges, Submissions and Grader system"

    def ready(self):
        # load subcategories and update their max_xp
        self.__update_subcategories_max_xp()
        # TODO: Assert SubcategoryProficiencyAwards exist for each subcategory

    def __update_subcategories_max_xp(self):
        """
        Go through every challenge for every subcategory, figure out the maximum score that a user can
            get from a subcategory and update its field
        This is done to update max_xp on the SubCategory model when we've added new challenges
        """
        from challenges.models import SubCategory, Challenge
        subcategories = SubCategory.objects.all()
        for subcategory in subcategories:
            maximum_score = sum(challenge.score for challenge in subcategory.challenges.all())
            subcategory.max_score = maximum_score
            subcategory.save()
