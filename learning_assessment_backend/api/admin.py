from django.contrib import admin

from .models import (
    UserProfile,
    Tag,
    Question,
    QuestionOption,
    Quiz,
    QuizQuestion,
    QuizSession,
    SessionParticipant,
    SessionAnswer,
    MemoryGame,
    MemoryCard,
    MemorySession,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "updated_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "question_type", "difficulty", "is_active", "created_at")
    list_filter = ("question_type", "difficulty", "is_active")
    search_fields = ("text",)
    inlines = [QuestionOptionInline]
    filter_horizontal = ("tags",)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_exam", "is_published", "created_at")
    list_filter = ("is_exam", "is_published")
    search_fields = ("title",)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "question", "order", "points")
    list_filter = ("quiz",)


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "quiz", "status", "current_order", "created_at")
    list_filter = ("status", "quiz")


@admin.register(SessionParticipant)
class SessionParticipantAdmin(admin.ModelAdmin):
    list_display = ("session", "user", "score", "joined_at")
    list_filter = ("session",)


@admin.register(SessionAnswer)
class SessionAnswerAdmin(admin.ModelAdmin):
    list_display = ("participant", "question", "is_correct", "points_awarded", "answered_at")
    list_filter = ("is_correct",)


class MemoryCardInline(admin.TabularInline):
    model = MemoryCard
    extra = 0


@admin.register(MemoryGame)
class MemoryGameAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    inlines = [MemoryCardInline]


@admin.register(MemorySession)
class MemorySessionAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "user", "moves_count", "matched_pairs_count", "started_at")
    list_filter = ("game",)
