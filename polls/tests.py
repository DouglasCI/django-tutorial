import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice


def create_question(question_text, days, choices=None):
  """
  Create a question with the given `question_text` and published the
  given number of `days` offset to now (negative for questions published
  in the past, positive for questions that have yet to be published).
  """
  if choices is None:
    choices = [{"choice_text": "Choice", "votes": 0}]
  
  time = timezone.now() + datetime.timedelta(days=days)
  q = Question.objects.create(question_text=question_text, pub_date=time)
  
  for c in choices:
    Choice.objects.create(question=q, choice_text=c["choice_text"], votes=c["votes"])
    
  return q

class QuestionIndexViewTests(TestCase):
  def test_no_questions(self):
    """
    If no questions exist, an appropriate message is displayed.
    """
    response = self.client.get(reverse("polls:index"))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "No polls are available.")
    self.assertQuerySetEqual(response.context["latest_question_list"], [])

  def test_past_question(self):
    """
    Questions with a pub_date in the past are displayed on the
    index page.
    """
    question = create_question(question_text="Past question.", days=-30)
    response = self.client.get(reverse("polls:index"))
    self.assertQuerySetEqual(
        response.context["latest_question_list"],
        [question],
    )

  def test_future_question(self):
    """
    Questions with a pub_date in the future aren't displayed on
    the index page.
    """
    create_question(question_text="Future question.", days=30)
    response = self.client.get(reverse("polls:index"))
    self.assertContains(response, "No polls are available.")
    self.assertQuerySetEqual(response.context["latest_question_list"], [])

  def test_future_question_and_past_question(self):
    """
    Even if both past and future questions exist, only past questions
    are displayed.
    """
    question = create_question(question_text="Past question.", days=-30)
    create_question(question_text="Future question.", days=30)
    response = self.client.get(reverse("polls:index"))
    self.assertQuerySetEqual(
        response.context["latest_question_list"],
        [question],
    )

  def test_two_past_questions(self):
    """
    The questions index page may display multiple questions.
    """
    question1 = create_question(question_text="Past question 1.", days=-30)
    question2 = create_question(question_text="Past question 2.", days=-5)
    response = self.client.get(reverse("polls:index"))
    self.assertQuerySetEqual(
        response.context["latest_question_list"],
        [question2, question1],
    )
  
  def test_question_with_choice(self):
    """
    Display questions with choices.
    """
    question_with_choice = create_question(question_text="With choices.", days=-1)
    response = self.client.get(reverse("polls:index"))
    self.assertEqual(response.status_code, 200)
    self.assertQuerySetEqual(
      response.context["latest_question_list"],
      [question_with_choice]
    )
    
  def test_question_without_choices(self):
    """
    Don't display questions without choices.
    """
    create_question(question_text="Without choices.", days=-1, choices=[])
    response = self.client.get(reverse("polls:index"))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "No polls are available.")
    self.assertQuerySetEqual(response.context["latest_question_list"], [])
    
  def test_question_with_and_without_choices(self):
    """
    Only display questions with choices and 
    don't display the ones without.
    """
    question_with_choice = create_question(question_text="With choices.", days=-1)
    create_question(question_text="Without choices.", days=-1, choices=[])
    response = self.client.get(reverse("polls:index"))
    self.assertEqual(response.status_code, 200)
    self.assertQuerySetEqual(
      response.context["latest_question_list"],
      [question_with_choice]
    )
    
class QuestionDetailViewTests(TestCase):
  def test_future_question(self):
    """
    The detail view of a question with a pub_date in the future
    returns a 404 not found.
    """
    future_question = create_question(question_text="Future question.", days=5)
    response = self.client.get(reverse("polls:detail", args=(future_question.pk,)))
    self.assertEqual(response.status_code, 404)
    
  def test_past_question(self):
    """
    The detail view of a question with a pub_date in the past
    displays the question's text.
    """
    past_question = create_question(question_text="Past question.", days=-5)
    response = self.client.get(reverse("polls:detail", args=(past_question.pk,)))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, past_question.question_text)
    
  def test_question_with_choice(self):
    """
    The detail view of a question with a choice.
    """
    question_with_choice = create_question(question_text="With choices.", days=-1)
    response = self.client.get(reverse("polls:detail", args=(question_with_choice.pk,)))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, question_with_choice.question_text)
    
  def test_question_without_choice(self):
    """
    The detail view of a question without any choices.
    """
    question_without_choices = create_question(
      question_text="With choices.", days=-1, choices=[]
    )
    response = self.client.get(reverse("polls:detail", args=(question_without_choices.pk,)))
    self.assertEqual(response.status_code, 404)

class QuestionModelTests(TestCase):
  def test_was_published_recently_with_future_question(self):
    """
    was_published_recently() returns False for questions whose pub_date
    is in the future.
    """
    time = timezone.now() + datetime.timedelta(days=30)
    future_question = Question(pub_date=time)
    self.assertIs(future_question.was_published_recently(), False)
  
  def test_was_published_recently_with_old_question(self):
    time = timezone.now() - datetime.timedelta(days=1, seconds=1)
    old_question = Question(pub_date=time)
    self.assertIs(old_question.was_published_recently(), False)
    
  def test_was_published_recently_with_recent_question(self):
    time = timezone.now() - datetime.timedelta(minutes=1)
    recent_question = Question(pub_date=time)
    self.assertIs(recent_question.was_published_recently(), True)
    