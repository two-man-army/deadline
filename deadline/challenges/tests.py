from django.test import TestCase
from django.core.exceptions import ValidationError

from challenges.models import Challenge


# Create your tests here.
class ChallengesModelTest(TestCase):
    def test_absolute_url(self):
        c = Challenge(name='Hello', rating=5, score=10)
        expected_url = '/challenge/{}'.format(c.id)
        self.assertEqual(c.get_absolute_url(), expected_url)

    def test_cannot_save_duplicate_challenge(self):
        c = Challenge(name='Hello', rating=5, score=10)
        c.save()
        with self.assertRaises(ValidationError):
            c = Challenge(name='Hello', rating=5, score=10)
            c.full_clean()

    def test_cannot_save_blank_challenge(self):
        c = Challenge()
        with self.assertRaises(Exception):
            c.full_clean()
