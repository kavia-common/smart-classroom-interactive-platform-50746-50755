from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class UserProfile(models.Model):
    """
    Stores application role + preferences for a user.

    Roles:
    - ADMIN: platform administrator (can manage everything)
    - TEACHER: manages question bank, quizzes, sessions
    - STUDENT: participates in sessions/games
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT)
    preferences = models.JSONField(default=dict, blank=True)  # accessibility + UI prefs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user.username} ({self.role})"


@receiver(post_save, sender=User)
def _ensure_profile(sender, instance, created, **kwargs):
    """Ensure every user has a profile row."""
    if created:
        UserProfile.objects.create(user=instance)


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Question(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "EASY", "Easy"
        MEDIUM = "MEDIUM", "Medium"
        HARD = "HARD", "Hard"

    class QuestionType(models.TextChoices):
        MCQ = "MCQ", "Multiple Choice"
        TRUE_FALSE = "TRUE_FALSE", "True/False"
        SHORT = "SHORT", "Short Answer"

    text = models.TextField()
    question_type = models.CharField(max_length=16, choices=QuestionType.choices, default=QuestionType.MCQ)
    difficulty = models.CharField(max_length=16, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    tags = models.ManyToManyField(Tag, blank=True, related_name="questions")
    media_url = models.URLField(blank=True, null=True)  # optional media reference
    explanation = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_questions"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Question {self.id}"


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)

    def __str__(self) -> str:  # pragma: no cover
        return f"Option {self.id} (Q{self.question_id})"


class Quiz(models.Model):
    """
    A quiz or an exam.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    is_exam = models.BooleanField(default=False)
    time_limit_seconds = models.IntegerField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_quizzes"
    )
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.title


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="quiz_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="in_quizzes")
    order = models.PositiveIntegerField(default=0)
    points = models.IntegerField(default=1)

    class Meta:
        unique_together = ("quiz", "question")
        ordering = ["order"]


class QuizSession(models.Model):
    """
    A teacher-led delivery session for a quiz/exam.
    """
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="sessions")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_sessions"
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    current_order = models.PositiveIntegerField(default=0)  # teacher-controlled navigation
    allow_student_navigation = models.BooleanField(default=False)

    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SessionParticipant(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="session_participations")
    joined_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("session", "user")


class SessionAnswer(models.Model):
    participant = models.ForeignKey(SessionParticipant, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_options = models.ManyToManyField(QuestionOption, blank=True, related_name="selected_in_answers")
    answer_text = models.TextField(blank=True, default="")
    is_correct = models.BooleanField(blank=True, null=True)  # null for ungraded (e.g., SHORT)
    points_awarded = models.IntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("participant", "question")


class MemoryGame(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_memory_games"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class MemoryCard(models.Model):
    """
    Each pair shares a match_key.
    """
    game = models.ForeignKey(MemoryGame, on_delete=models.CASCADE, related_name="cards")
    match_key = models.CharField(max_length=64)
    label = models.CharField(max_length=200, blank=True, default="")
    media_url = models.URLField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["game", "match_key"])]


class MemorySession(models.Model):
    """
    A memory-game play session (per student).
    state schema (JSON):
    {
      "open_card_ids": [1,2],
      "matched_card_ids": [3,4],
      "turn": 1
    }
    """
    game = models.ForeignKey(MemoryGame, on_delete=models.CASCADE, related_name="sessions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memory_sessions")
    state = models.JSONField(default=dict, blank=True)
    moves_count = models.PositiveIntegerField(default=0)
    matched_pairs_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("game", "user")
