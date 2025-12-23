from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Tag,
    Question,
    Quiz,
    QuizQuestion,
    QuizSession,
    SessionParticipant,
    SessionAnswer,
    MemoryGame,
    MemoryCard,
    MemorySession,
)
from .permissions import IsTeacher
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    RegisterSerializer,
    AuthTokenSerializer,
    TagSerializer,
    QuestionSerializer,
    QuizSerializer,
    QuizSessionSerializer,
    SessionParticipantSerializer,
    SessionAnswerSerializer,
    MemoryGameSerializer,
    MemorySessionSerializer,
)

User = get_user_model()


class MeView(APIView):
    """
    Returns the current authenticated user (including role/preferences).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class AuthViewSet(viewsets.ViewSet):
    """
    Token-based authentication endpoints (register/login/logout).

    - POST /api/auth/register/
    - POST /api/auth/login/
    - POST /api/auth/logout/
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(username=serializer.validated_data["username"], password=serializer.validated_data["password"])
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="logout")
    def logout(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Logged out"})


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer

    def get_permissions(self):
        # Students can view tags; teachers/admin can manage tags.
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsTeacher()]


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().prefetch_related("tags", "options")
    serializer_class = QuestionSerializer

    def get_permissions(self):
        # Students can list/retrieve active questions; teachers/admin full CRUD.
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsTeacher()]

    def get_queryset(self):
        qs = super().get_queryset()
        # Basic filtering via query params
        tag_ids = self.request.query_params.getlist("tag")
        difficulty = self.request.query_params.get("difficulty")
        qtype = self.request.query_params.get("question_type")
        active_only = self.request.query_params.get("active_only", "true").lower() in ("1", "true", "yes")

        if active_only:
            qs = qs.filter(is_active=True)
        if tag_ids:
            qs = qs.filter(tags__id__in=tag_ids).distinct()
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if qtype:
            qs = qs.filter(question_type=qtype)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all().prefetch_related("quiz_questions__question__options", "quiz_questions__question__tags")
    serializer_class = QuizSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsTeacher()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"], permission_classes=[IsTeacher], url_path="report")
    def report(self, request, pk=None):
        """
        Teacher reporting endpoint for a quiz: summarizes sessions + participant scores.
        """
        quiz = self.get_object()
        sessions = quiz.sessions.all().order_by("-created_at")
        payload = []
        for s in sessions:
            participants = s.participants.select_related("user").all()
            payload.append(
                {
                    "session_id": s.id,
                    "status": s.status,
                    "created_at": s.created_at,
                    "participants": [
                        {"user_id": p.user_id, "username": p.user.username, "score": p.score, "joined_at": p.joined_at}
                        for p in participants
                    ],
                }
            )
        return Response({"quiz_id": quiz.id, "quiz_title": quiz.title, "sessions": payload})


class QuizSessionViewSet(viewsets.ModelViewSet):
    queryset = QuizSession.objects.all().select_related("quiz", "created_by")
    serializer_class = QuizSessionSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "current_question", "join", "submit_answer"):
            return [IsAuthenticated()]
        return [IsTeacher()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsTeacher], url_path="start")
    def start(self, request, pk=None):
        session = self.get_object()
        if session.status == QuizSession.Status.COMPLETED:
            return Response({"detail": "Session already completed"}, status=status.HTTP_400_BAD_REQUEST)
        session.status = QuizSession.Status.ACTIVE
        if not session.started_at:
            session.started_at = timezone.now()
        session.save()
        return Response(QuizSessionSerializer(session).data)

    @action(detail=True, methods=["post"], permission_classes=[IsTeacher], url_path="end")
    def end(self, request, pk=None):
        session = self.get_object()
        session.status = QuizSession.Status.COMPLETED
        session.ended_at = timezone.now()
        session.save()
        return Response(QuizSessionSerializer(session).data)

    @action(detail=True, methods=["post"], permission_classes=[IsTeacher], url_path="advance")
    def advance(self, request, pk=None):
        session = self.get_object()
        total = session.quiz.quiz_questions.count()
        if total == 0:
            return Response({"detail": "Quiz has no questions"}, status=status.HTTP_400_BAD_REQUEST)
        session.current_order = min(session.current_order + 1, total - 1)
        session.save()
        return Response({"current_order": session.current_order})

    @action(detail=True, methods=["post"], permission_classes=[IsTeacher], url_path="set-current")
    def set_current(self, request, pk=None):
        session = self.get_object()
        try:
            order = int(request.data.get("order"))
        except Exception:
            return Response({"detail": "order must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
        total = session.quiz.quiz_questions.count()
        if order < 0 or order >= total:
            return Response({"detail": "order out of range"}, status=status.HTTP_400_BAD_REQUEST)
        session.current_order = order
        session.save()
        return Response({"current_order": session.current_order})

    @action(detail=True, methods=["get"], url_path="current-question")
    def current_question(self, request, pk=None):
        session = self.get_object()
        qq = session.quiz.quiz_questions.order_by("order")[session.current_order : session.current_order + 1].first()
        if not qq:
            return Response({"detail": "No current question"}, status=status.HTTP_404_NOT_FOUND)
        # Reuse QuestionSerializer data
        return Response(
            {
                "session_id": session.id,
                "status": session.status,
                "current_order": session.current_order,
                "question": QuestionSerializer(qq.question).data,
                "points": qq.points,
            }
        )

    @action(detail=True, methods=["post"], url_path="join")
    def join(self, request, pk=None):
        session = self.get_object()
        participant, _ = SessionParticipant.objects.get_or_create(session=session, user=request.user)
        return Response(SessionParticipantSerializer(participant).data)

    @action(detail=True, methods=["post"], url_path="submit-answer")
    def submit_answer(self, request, pk=None):
        """
        Student submits an answer. Auto-grading supported for MCQ and TRUE_FALSE.
        SHORT answers are stored but left ungraded (is_correct=None).
        """
        session = self.get_object()
        participant, _ = SessionParticipant.objects.get_or_create(session=session, user=request.user)

        serializer = SessionAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        selected_options = serializer.validated_data.get("selected_options", [])
        answer_text = serializer.validated_data.get("answer_text", "")

        # ensure question belongs to quiz
        qq = QuizQuestion.objects.filter(quiz=session.quiz, question=question).first()
        if not qq:
            return Response({"detail": "Question not part of this quiz"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            ans, _created = SessionAnswer.objects.get_or_create(participant=participant, question=question)
            ans.answer_text = answer_text

            # reset selected options
            ans.selected_options.clear()
            if selected_options:
                ans.selected_options.set(selected_options)

            # grade
            is_correct = None
            points_awarded = 0
            if question.question_type in (Question.QuestionType.MCQ, Question.QuestionType.TRUE_FALSE):
                correct_ids = set(question.options.filter(is_correct=True).values_list("id", flat=True))
                chosen_ids = set([o.id for o in selected_options])
                is_correct = (correct_ids == chosen_ids) and len(correct_ids) > 0
                points_awarded = qq.points if is_correct else 0

            ans.is_correct = is_correct
            ans.points_awarded = points_awarded
            ans.save()

            # recompute participant score
            participant.score = sum(participant.answers.values_list("points_awarded", flat=True))
            participant.save()

        return Response(
            {
                "answer": SessionAnswerSerializer(ans).data,
                "participant_score": participant.score,
            }
        )

    @action(detail=True, methods=["get"], permission_classes=[IsTeacher], url_path="results")
    def results(self, request, pk=None):
        session = self.get_object()
        participants = session.participants.select_related("user").all().order_by("-score", "joined_at")
        return Response(
            {
                "session": QuizSessionSerializer(session).data,
                "participants": [
                    {"user_id": p.user_id, "username": p.user.username, "score": p.score, "joined_at": p.joined_at}
                    for p in participants
                ],
            }
        )


class PreferenceViewSet(viewsets.ViewSet):
    """
    Access / update the current user's preferences (stored in UserProfile.preferences JSON).
    """
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        return Response(UserProfileSerializer(request.user.profile).data)

    def partial_update(self, request, pk=None):
        profile = request.user.profile
        patch = request.data.get("preferences", request.data)
        if not isinstance(patch, dict):
            return Response({"detail": "preferences must be an object"}, status=status.HTTP_400_BAD_REQUEST)

        prefs = profile.preferences or {}
        prefs.update(patch)
        profile.preferences = prefs
        profile.save()
        return Response(UserProfileSerializer(profile).data)


class MemoryGameViewSet(viewsets.ModelViewSet):
    queryset = MemoryGame.objects.all().prefetch_related("cards")
    serializer_class = MemoryGameSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsTeacher()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="start")
    def start(self, request, pk=None):
        game = self.get_object()
        session, _ = MemorySession.objects.get_or_create(game=game, user=request.user)
        # initialize state if empty
        if not session.state:
            session.state = {"open_card_ids": [], "matched_card_ids": [], "turn": 1}
            session.save()
        return Response(MemorySessionSerializer(session).data)


class MemorySessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MemorySession.objects.all().select_related("game", "user")
    serializer_class = MemorySessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Students can only see their own sessions; teachers/admin can see all.
        user = self.request.user
        role = getattr(getattr(user, "profile", None), "role", None)
        if user.is_superuser or user.is_staff or role == "ADMIN" or role == "TEACHER":
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    @action(detail=True, methods=["post"], url_path="flip")
    def flip(self, request, pk=None):
        """
        Flip a card in a memory session.

        Body:
        - card_id: int
        """
        session = self.get_object()
        card_id = request.data.get("card_id")
        try:
            card_id = int(card_id)
        except Exception:
            return Response({"detail": "card_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        card = MemoryCard.objects.filter(id=card_id, game=session.game).first()
        if not card:
            return Response({"detail": "Card not found for this game"}, status=status.HTTP_404_NOT_FOUND)

        state = session.state or {"open_card_ids": [], "matched_card_ids": [], "turn": 1}
        open_ids = state.get("open_card_ids", [])
        matched_ids = set(state.get("matched_card_ids", []))
        turn = int(state.get("turn", 1))

        if card_id in matched_ids:
            return Response({"detail": "Card already matched", "state": state}, status=status.HTTP_200_OK)

        if card_id in open_ids:
            return Response({"detail": "Card already open", "state": state}, status=status.HTTP_200_OK)

        open_ids.append(card_id)

        is_match = None
        if len(open_ids) == 2:
            c1 = MemoryCard.objects.get(id=open_ids[0])
            c2 = MemoryCard.objects.get(id=open_ids[1])
            if c1.match_key == c2.match_key:
                matched_ids.update(open_ids)
                session.matched_pairs_count += 1
                is_match = True
            else:
                is_match = False

            session.moves_count += 1
            open_ids = []
            turn += 1

        state["open_card_ids"] = open_ids
        state["matched_card_ids"] = list(matched_ids)
        state["turn"] = turn
        session.state = state
        session.save()

        return Response({"state": state, "is_match": is_match, "moves_count": session.moves_count, "matched_pairs_count": session.matched_pairs_count})
