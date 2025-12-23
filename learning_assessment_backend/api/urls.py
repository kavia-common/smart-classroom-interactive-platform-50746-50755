from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import health
from .viewsets import (
    MeView,
    AuthViewSet,
    TagViewSet,
    QuestionViewSet,
    QuizViewSet,
    QuizSessionViewSet,
    MemoryGameViewSet,
    MemorySessionViewSet,
    PreferenceViewSet,
)

router = DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"tags", TagViewSet, basename="tags")
router.register(r"questions", QuestionViewSet, basename="questions")
router.register(r"quizzes", QuizViewSet, basename="quizzes")
router.register(r"sessions", QuizSessionViewSet, basename="sessions")
router.register(r"memory-games", MemoryGameViewSet, basename="memory-games")
router.register(r"memory-sessions", MemorySessionViewSet, basename="memory-sessions")

urlpatterns = [
    path("health/", health, name="Health"),
    path("me/", MeView.as_view(), name="me"),
    # Preferences: implemented as a ViewSet with retrieve/partial_update semantics
    path("preferences/", PreferenceViewSet.as_view({"get": "retrieve", "patch": "partial_update"}), name="preferences"),
    path("", include(router.urls)),
]
