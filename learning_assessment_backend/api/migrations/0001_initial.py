# Generated manually for initial schema.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MemoryGame",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_memory_games",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Quiz",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("is_exam", models.BooleanField(default=False)),
                ("time_limit_seconds", models.IntegerField(blank=True, null=True)),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_quizzes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField()),
                ("question_type", models.CharField(choices=[("MCQ", "Multiple Choice"), ("TRUE_FALSE", "True/False"), ("SHORT", "Short Answer")], default="MCQ", max_length=16)),
                ("difficulty", models.CharField(choices=[("EASY", "Easy"), ("MEDIUM", "Medium"), ("HARD", "Hard")], default="MEDIUM", max_length=16)),
                ("media_url", models.URLField(blank=True, null=True)),
                ("explanation", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_questions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("tags", models.ManyToManyField(blank=True, related_name="questions", to="api.tag")),
            ],
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("ADMIN", "Admin"), ("TEACHER", "Teacher"), ("STUDENT", "Student")], default="STUDENT", max_length=16)),
                ("preferences", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="QuizSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("ACTIVE", "Active"), ("COMPLETED", "Completed")], default="DRAFT", max_length=16)),
                ("current_order", models.PositiveIntegerField(default=0)),
                ("allow_student_navigation", models.BooleanField(default=False)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sessions", to="api.quiz")),
            ],
        ),
        migrations.CreateModel(
            name="QuestionOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=512)),
                ("is_correct", models.BooleanField(default=False)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="options", to="api.question")),
            ],
        ),
        migrations.CreateModel(
            name="MemoryCard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("match_key", models.CharField(max_length=64)),
                ("label", models.CharField(blank=True, default="", max_length=200)),
                ("media_url", models.URLField(blank=True, null=True)),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cards", to="api.memorygame")),
            ],
            options={
                "indexes": [models.Index(fields=["game", "match_key"], name="api_memoryc_game_id_7b90d2_idx")],
            },
        ),
        migrations.CreateModel(
            name="MemorySession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("state", models.JSONField(blank=True, default=dict)),
                ("moves_count", models.PositiveIntegerField(default=0)),
                ("matched_pairs_count", models.PositiveIntegerField(default=0)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sessions", to="api.memorygame")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memory_sessions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "unique_together": {("game", "user")},
            },
        ),
        migrations.CreateModel(
            name="SessionParticipant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("score", models.IntegerField(default=0)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="api.quizsession")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="session_participations", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "unique_together": {("session", "user")},
            },
        ),
        migrations.CreateModel(
            name="QuizQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField(default=0)),
                ("points", models.IntegerField(default=1)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="in_quizzes", to="api.question")),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_questions", to="api.quiz")),
            ],
            options={
                "ordering": ["order"],
                "unique_together": {("quiz", "question")},
            },
        ),
        migrations.CreateModel(
            name="SessionAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("answer_text", models.TextField(blank=True, default="")),
                ("is_correct", models.BooleanField(blank=True, null=True)),
                ("points_awarded", models.IntegerField(default=0)),
                ("answered_at", models.DateTimeField(auto_now_add=True)),
                ("participant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="api.sessionparticipant")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="api.question")),
                ("selected_options", models.ManyToManyField(blank=True, related_name="selected_in_answers", to="api.questionoption")),
            ],
            options={
                "unique_together": {("participant", "question")},
            },
        ),
    ]
