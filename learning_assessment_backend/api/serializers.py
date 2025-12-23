from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.authtoken.models import Token

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

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["role", "preferences", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "profile"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.Role.choices, required=False)

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data):
        role = validated_data.pop("role", UserProfile.Role.STUDENT)
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Profile is auto-created via signal; ensure role is set.
        user.profile.role = role
        user.profile.save()

        Token.objects.get_or_create(user=user)
        return user


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ["id", "text", "is_correct"]
        read_only_fields = ["id"]


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, required=False)
    tags = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Tag.objects.all())

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "question_type",
            "difficulty",
            "tags",
            "media_url",
            "explanation",
            "is_active",
            "options",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        tags = validated_data.pop("tags", [])
        question = Question.objects.create(**validated_data)
        if tags:
            question.tags.set(tags)
        for opt in options_data:
            QuestionOption.objects.create(question=question, **opt)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)
        tags = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if options_data is not None:
            instance.options.all().delete()
            for opt in options_data:
                QuestionOption.objects.create(question=instance, **opt)
        return instance


class QuizQuestionWriteSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    order = serializers.IntegerField(required=False, default=0)
    points = serializers.IntegerField(required=False, default=1)


class QuizQuestionReadSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()

    class Meta:
        model = QuizQuestion
        fields = ["id", "order", "points", "question"]


class QuizSerializer(serializers.ModelSerializer):
    quiz_questions = QuizQuestionReadSerializer(many=True, read_only=True)
    questions = QuizQuestionWriteSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "is_exam",
            "time_limit_seconds",
            "is_published",
            "created_by",
            "created_at",
            "quiz_questions",
            "questions",
        ]
        read_only_fields = ["id", "created_by", "created_at", "quiz_questions"]

    def create(self, validated_data):
        questions_payload = validated_data.pop("questions", [])
        quiz = Quiz.objects.create(**validated_data)
        for item in questions_payload:
            QuizQuestion.objects.create(
                quiz=quiz,
                question_id=item["question_id"],
                order=item.get("order", 0),
                points=item.get("points", 1),
            )
        return quiz

    def update(self, instance, validated_data):
        questions_payload = validated_data.pop("questions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if questions_payload is not None:
            instance.quiz_questions.all().delete()
            for item in questions_payload:
                QuizQuestion.objects.create(
                    quiz=instance,
                    question_id=item["question_id"],
                    order=item.get("order", 0),
                    points=item.get("points", 1),
                )
        return instance


class QuizSessionSerializer(serializers.ModelSerializer):
    participants_count = serializers.IntegerField(source="participants.count", read_only=True)

    class Meta:
        model = QuizSession
        fields = [
            "id",
            "quiz",
            "created_by",
            "status",
            "current_order",
            "allow_student_navigation",
            "started_at",
            "ended_at",
            "created_at",
            "participants_count",
        ]
        read_only_fields = ["id", "created_by", "started_at", "ended_at", "created_at", "participants_count"]


class SessionParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = SessionParticipant
        fields = ["id", "session", "user", "joined_at", "score"]
        read_only_fields = ["id", "joined_at", "score", "user"]


class SessionAnswerSerializer(serializers.ModelSerializer):
    selected_options = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=QuestionOption.objects.all())

    class Meta:
        model = SessionAnswer
        fields = ["id", "participant", "question", "selected_options", "answer_text", "is_correct", "points_awarded", "answered_at"]
        read_only_fields = ["id", "is_correct", "points_awarded", "answered_at"]


class MemoryCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoryCard
        fields = ["id", "match_key", "label", "media_url"]
        read_only_fields = ["id"]


class MemoryGameSerializer(serializers.ModelSerializer):
    cards = MemoryCardSerializer(many=True, required=False)

    class Meta:
        model = MemoryGame
        fields = ["id", "name", "description", "created_by", "created_at", "cards"]
        read_only_fields = ["id", "created_by", "created_at"]

    def create(self, validated_data):
        cards_data = validated_data.pop("cards", [])
        game = MemoryGame.objects.create(**validated_data)
        for card in cards_data:
            MemoryCard.objects.create(game=game, **card)
        return game

    def update(self, instance, validated_data):
        cards_data = validated_data.pop("cards", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if cards_data is not None:
            instance.cards.all().delete()
            for card in cards_data:
                MemoryCard.objects.create(game=instance, **card)
        return instance


class MemorySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemorySession
        fields = ["id", "game", "user", "state", "moves_count", "matched_pairs_count", "started_at", "ended_at"]
        read_only_fields = ["id", "user", "moves_count", "matched_pairs_count", "started_at", "ended_at"]
