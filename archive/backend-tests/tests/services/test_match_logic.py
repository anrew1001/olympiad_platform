"""Тесты для match logic с ELO системой (Phase 2)."""

import pytest
from datetime import datetime
from sqlalchemy import select

from app.models.match import Match, MatchAnswer
from app.models.user import User
from app.models.enums import MatchStatus
from app.services.match_logic import (
    finalize_match,
    finalize_match_forfeit,
    handle_technical_error,
    check_match_completion,
)


class TestFinalizeMatchCompletion:
    """Тесты для нормального завершения матча (reason='completion')."""

    @pytest.mark.asyncio
    async def test_equal_ratings_player1_wins(self, db_session, equal_rating_users, test_match):
        """Две равные рейтинги, Player1 выигрывает."""
        # Setup
        test_match.player1_score = 3
        test_match.player2_score = 2
        test_match.status = MatchStatus.ACTIVE

        # Act
        result = await finalize_match(test_match.id, db_session, reason="completion")
        await db_session.commit()

        # Assert
        assert result["winner_id"] == test_match.player1_id
        assert result["player1_rating_change"] > 0
        assert result["player2_rating_change"] < 0
        assert result["player1_rating_change"] + result["player2_rating_change"] == 0

        # Check match status
        match = await db_session.get(Match, test_match.id)
        assert match.status == MatchStatus.FINISHED
        assert match.finished_at is not None

    @pytest.mark.asyncio
    async def test_draw(self, db_session, test_users, test_match):
        """Ничья между равными рейтингами."""
        # Setup
        test_match.player1_score = 2
        test_match.player2_score = 2
        test_match.status = MatchStatus.ACTIVE

        # Act
        result = await finalize_match(test_match.id, db_session, reason="completion")

        # Assert
        assert result["winner_id"] is None
        assert result["player1_rating_change"] == 0
        assert result["player2_rating_change"] == 0

    @pytest.mark.asyncio
    async def test_upset_victory(self, db_session, skill_gap_users, test_tasks):
        """Слабый (1000) выигрывает у сильного (1200)."""
        # Setup: weak=1, strong=0 (по ID)
        match = Match(
            id=100,
            player1_id=skill_gap_users[0].id,  # strong 1200
            player2_id=skill_gap_users[1].id,  # weak 1000
            status=MatchStatus.ACTIVE,
            created_at=datetime.utcnow(),
            player1_score=1,  # Strong loses
            player2_score=4,  # Weak wins
        )
        db_session.add(match)
        await db_session.flush()

        # Act
        result = await finalize_match(match.id, db_session, reason="completion")

        # Assert
        # Weak should gain a lot, strong should lose a lot
        weak_change = result["player2_rating_change"]
        strong_change = result["player1_rating_change"]

        assert weak_change > 20, f"Weak should gain >20, got {weak_change}"
        assert strong_change < -20, f"Strong should lose >20, got {strong_change}"

    @pytest.mark.asyncio
    async def test_idempotency(self, db_session, test_users, test_match):
        """Вызов finalize_match дважды должен вернуть одинаковый результат."""
        # Setup
        test_match.player1_score = 3
        test_match.player2_score = 1
        test_match.status = MatchStatus.ACTIVE

        # Act: First call
        result1 = await finalize_match(test_match.id, db_session, reason="completion")
        await db_session.commit()

        # Verify it's finished
        match = await db_session.get(Match, test_match.id)
        assert match.status == MatchStatus.FINISHED

        # Act: Second call (should return cached result)
        result2 = await finalize_match(test_match.id, db_session, reason="completion")

        # Assert: Results should be identical
        assert result1["winner_id"] == result2["winner_id"]
        assert result1["player1_rating_change"] == result2["player1_rating_change"]
        assert result1["player2_rating_change"] == result2["player2_rating_change"]

        # Verify ratings weren't updated twice
        user1 = await db_session.get(User, test_users[0].id)
        assert user1.rating == 1000 + result1["player1_rating_change"]


class TestFinalizeMatchForfeit:
    """Тесты для завершения матча по forfeit (timeout disconnect)."""

    @pytest.mark.asyncio
    async def test_forfeit_player1_disconnects(self, db_session, equal_rating_users, test_match):
        """Player1 отключился и не переподключился - Player2 выигрывает."""
        # Setup
        test_match.status = MatchStatus.ACTIVE
        test_match.player1_score = 2
        test_match.player2_score = 2

        # Act: Player1 forfeits
        result = await finalize_match_forfeit(test_match.id, test_match.player1_id, db_session)
        await db_session.commit()

        # Assert
        assert result["winner_id"] == test_match.player2_id
        # Player2 выиграл - должен получить ELO
        assert result["player2_rating_change"] > 0
        # Player1 проиграл - должен потерять ELO
        assert result["player1_rating_change"] < 0

        # Verify match status
        match = await db_session.get(Match, test_match.id)
        assert match.status == MatchStatus.FINISHED
        assert match.winner_id == test_match.player2_id

    @pytest.mark.asyncio
    async def test_forfeit_player2_disconnects(self, db_session, equal_rating_users, test_match):
        """Player2 отключился - Player1 выигрывает."""
        # Act
        result = await finalize_match_forfeit(test_match.id, test_match.player2_id, db_session)

        # Assert
        assert result["winner_id"] == test_match.player1_id
        assert result["player1_rating_change"] > 0
        assert result["player2_rating_change"] < 0

    @pytest.mark.asyncio
    async def test_forfeit_invalid_user(self, db_session, test_match):
        """Попытка forfeit для пользователя не участвующего в матче."""
        # Act & Assert
        with pytest.raises(ValueError, match="not a participant"):
            await finalize_match_forfeit(test_match.id, 9999, db_session)


class TestHandleTechnicalError:
    """Тесты для обработки технических ошибок."""

    @pytest.mark.asyncio
    async def test_both_disconnected(self, db_session, test_users, test_match):
        """Оба игрока отключились - статус ERROR, рейтинги без изменений."""
        # Setup
        user1_old_rating = test_users[0].rating
        user2_old_rating = test_users[1].rating
        test_match.status = MatchStatus.ACTIVE

        # Act
        await handle_technical_error(test_match.id, db_session, "Both players disconnected")
        await db_session.commit()

        # Assert: Match status should be ERROR
        match = await db_session.get(Match, test_match.id)
        assert match.status == MatchStatus.ERROR
        assert match.player1_rating_change == 0
        assert match.player2_rating_change == 0

        # Verify ratings unchanged
        user1 = await db_session.get(User, test_users[0].id)
        user2 = await db_session.get(User, test_users[1].id)
        assert user1.rating == user1_old_rating
        assert user2.rating == user2_old_rating

    @pytest.mark.asyncio
    async def test_technical_error_does_not_finalize_twice(self, db_session, test_match):
        """Вызов handle_technical_error дважды должен быть идемпотентным."""
        # Act: First call
        await handle_technical_error(test_match.id, db_session, "Error 1")
        await db_session.commit()

        # Verify it's ERROR
        match = await db_session.get(Match, test_match.id)
        assert match.status == MatchStatus.ERROR

        # Act: Second call (should raise or handle gracefully)
        with pytest.raises(ValueError, match="ERROR state"):
            await handle_technical_error(test_match.id, db_session, "Error 2")


class TestCheckMatchCompletion:
    """Тесты для проверки завершения матча."""

    @pytest.mark.asyncio
    async def test_match_not_complete_some_missing(self, db_session, test_users, test_match):
        """Матч не завершён - не все игроки ответили на все задачи."""
        # Setup: только Player1 ответил на 1-3 задачи
        for task_id in [1, 2, 3]:
            answer = MatchAnswer(
                match_id=test_match.id,
                user_id=test_users[0].id,
                task_id=task_id,
                answer="test",
                is_correct=True,
            )
            db_session.add(answer)

        await db_session.commit()

        # Act
        is_complete = await check_match_completion(test_match.id, db_session)

        # Assert
        assert is_complete is False

    @pytest.mark.asyncio
    async def test_match_complete_both_answered_all(self, db_session, test_users, test_match):
        """Матч завершён - оба ответили на все 5 задач."""
        # Setup: оба ответили на все 5 задач
        for user_id in [test_users[0].id, test_users[1].id]:
            for task_id in range(1, 6):
                answer = MatchAnswer(
                    match_id=test_match.id,
                    user_id=user_id,
                    task_id=task_id,
                    answer="test",
                    is_correct=True if task_id <= 3 else False,
                )
                db_session.add(answer)

        await db_session.commit()

        # Act
        is_complete = await check_match_completion(test_match.id, db_session)

        # Assert
        assert is_complete is True

    @pytest.mark.asyncio
    async def test_match_scores_calculated(self, db_session, test_users, test_match):
        """Проверить что scores рассчитаны правильно."""
        # Setup
        for user_id in [test_users[0].id, test_users[1].id]:
            for task_id in range(1, 6):
                is_correct = (user_id == test_users[0].id and task_id <= 4) or \
                             (user_id == test_users[1].id and task_id <= 3)
                answer = MatchAnswer(
                    match_id=test_match.id,
                    user_id=user_id,
                    task_id=task_id,
                    answer="test",
                    is_correct=is_correct,
                )
                db_session.add(answer)

        await db_session.commit()

        # Act
        is_complete = await check_match_completion(test_match.id, db_session)

        # Assert
        assert is_complete is True

        # Check scores
        match = await db_session.get(Match, test_match.id)
        assert match.player1_score == 4  # 4 correct
        assert match.player2_score == 3  # 3 correct


class TestExtremeRatings:
    """Тесты с экстремальными рейтингами."""

    @pytest.mark.asyncio
    async def test_extreme_rating_difference_master_wins(self, db_session, extreme_rating_users):
        """Master (2000) выигрывает у Novice (800) - минимальный gain."""
        # Setup
        match = Match(
            id=200,
            player1_id=extreme_rating_users[0].id,  # master 2000
            player2_id=extreme_rating_users[1].id,  # novice 800
            status=MatchStatus.ACTIVE,
            created_at=datetime.utcnow(),
            player1_score=5,
            player2_score=0,
        )
        db_session.add(match)
        await db_session.flush()

        # Act
        result = await finalize_match(match.id, db_session, reason="completion")

        # Assert
        master_gain = result["player1_rating_change"]
        novice_loss = result["player2_rating_change"]

        # Master должен получить мало (3-4 points)
        assert 0 < master_gain <= 4
        # Novice должен потерять много (28-32 points)
        assert -32 <= novice_loss < -28

    @pytest.mark.asyncio
    async def test_extreme_rating_difference_upset(self, db_session, extreme_rating_users):
        """Novice (800) выигрывает у Master (2000) - HUGE gain!"""
        # Setup
        match = Match(
            id=201,
            player1_id=extreme_rating_users[0].id,  # master 2000
            player2_id=extreme_rating_users[1].id,  # novice 800
            status=MatchStatus.ACTIVE,
            created_at=datetime.utcnow(),
            player1_score=0,
            player2_score=5,
        )
        db_session.add(match)
        await db_session.flush()

        # Act
        result = await finalize_match(match.id, db_session, reason="completion")

        # Assert
        master_loss = result["player1_rating_change"]
        novice_gain = result["player2_rating_change"]

        # Master должен потерять много
        assert master_loss < -28
        # Novice должен получить много
        assert novice_gain > 28
