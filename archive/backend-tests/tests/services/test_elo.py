"""Тесты для ELO рейтинг системы (Phase 1)."""

import pytest
from app.services.elo import (
    calculate_expected_score,
    calculate_rating_change,
    calculate_match_rating_changes,
    apply_rating_bounds,
)


class TestExpectedScore:
    """Тесты для расчёта ожидаемого результата."""

    def test_equal_ratings(self):
        """Игроки с одинаковыми рейтингами должны иметь 50% вероятность."""
        expected = calculate_expected_score(1000, 1000)
        assert 0.49 < expected < 0.51, f"Expected ~0.5, got {expected}"

    def test_strong_vs_weak(self):
        """Сильный игрок должен иметь высокий шанс победы."""
        strong = calculate_expected_score(1200, 1000)
        weak = calculate_expected_score(1000, 1200)

        assert strong > 0.5, "Strong player should have >50% chance"
        assert weak < 0.5, "Weak player should have <50% chance"
        assert strong + weak == pytest.approx(1.0), "Probabilities should sum to 1"

    def test_extreme_difference(self):
        """Экстремальная разница рейтинга должна быть capped."""
        master = calculate_expected_score(2000, 800)
        novice = calculate_expected_score(800, 2000)

        # Должны быть capped на 0.999 и 0.001
        assert master > 0.99, f"Master should have ~99.9% chance, got {master}"
        assert novice < 0.01, f"Novice should have ~0.1% chance, got {novice}"

    def test_symmetry(self):
        """E_a + E_b должна равняться 1."""
        for r1, r2 in [(800, 1200), (900, 900), (700, 2000)]:
            e1 = calculate_expected_score(r1, r2)
            e2 = calculate_expected_score(r2, r1)
            assert e1 + e2 == pytest.approx(1.0, abs=0.001)


class TestRatingChange:
    """Тесты для расчёта изменения рейтинга."""

    def test_win_equal_ratings(self):
        """Победа между равными игроками → +16."""
        change = calculate_rating_change(1000, 1000, outcome=1.0)
        # K=32, E=0.5, ΔR = 32 × (1 - 0.5) = 16
        assert change == 16

    def test_loss_equal_ratings(self):
        """Поражение между равными игроками → -16."""
        change = calculate_rating_change(1000, 1000, outcome=0.0)
        # K=32, E=0.5, ΔR = 32 × (0 - 0.5) = -16
        assert change == -16

    def test_draw_equal_ratings(self):
        """Ничья между равными игроками → 0."""
        change = calculate_rating_change(1000, 1000, outcome=0.5)
        # K=32, E=0.5, ΔR = 32 × (0.5 - 0.5) = 0
        assert change == 0

    def test_upset_victory(self):
        """Слабый игрок выигрывает у сильного → большой прирост."""
        weak_change = calculate_rating_change(800, 1200, outcome=1.0)
        strong_change = calculate_rating_change(1200, 800, outcome=0.0)

        # Слабый должен получить больше за победу
        assert weak_change > 20, f"Weak should gain >20, got {weak_change}"
        # Сильный должен потерять больше за поражение
        assert strong_change < -20, f"Strong should lose >20, got {strong_change}"

    def test_expected_victory(self):
        """Сильный выигрывает у слабого → маленький прирост."""
        strong_change = calculate_rating_change(1200, 800, outcome=1.0)
        weak_change = calculate_rating_change(800, 1200, outcome=0.0)

        # Сильный получает мало за ожидаемую победу
        assert strong_change < 16, f"Strong should gain <16, got {strong_change}"
        # Слабый теряет мало за ожидаемое поражение
        assert weak_change > -16, f"Weak should lose <16, got {weak_change}"

    def test_minimum_change(self):
        """Минимальное изменение не может быть < -32."""
        # Даже в худшем случае для мастера
        change = calculate_rating_change(2000, 800, outcome=0.0)
        assert change >= -32, f"Change should be >= -32, got {change}"

    def test_rating_bounds(self):
        """Минимальный рейтинг = 100."""
        assert apply_rating_bounds(50) == 100
        assert apply_rating_bounds(100) == 100
        assert apply_rating_bounds(150) == 150
        # Нет максимума
        assert apply_rating_bounds(5000) == 5000


class TestMatchRatingChanges:
    """Тесты для расчёта изменений рейтинга для обоих игроков."""

    def test_equal_ratings_player1_wins(self):
        """Player1 выигрывает против равного оппонента."""
        p1_change, p2_change = calculate_match_rating_changes(
            1000, 1000,
            winner_id=1,
            p1_id=1, p2_id=2
        )

        assert p1_change == 16, f"P1 should gain 16, got {p1_change}"
        assert p2_change == -16, f"P2 should lose 16, got {p2_change}"
        assert p1_change + p2_change == 0, "Total change should be zero-sum"

    def test_equal_ratings_player2_wins(self):
        """Player2 выигрывает против равного оппонента."""
        p1_change, p2_change = calculate_match_rating_changes(
            1000, 1000,
            winner_id=2,
            p1_id=1, p2_id=2
        )

        assert p1_change == -16, f"P1 should lose 16, got {p1_change}"
        assert p2_change == 16, f"P2 should gain 16, got {p2_change}"

    def test_draw(self):
        """Ничья между равными игроками."""
        p1_change, p2_change = calculate_match_rating_changes(
            1000, 1000,
            winner_id=None,
            p1_id=1, p2_id=2
        )

        assert p1_change == 0, f"P1 should get 0, got {p1_change}"
        assert p2_change == 0, f"P2 should get 0, got {p2_change}"

    def test_skill_gap_strong_wins(self):
        """Сильный (1200) выигрывает у слабого (1000)."""
        p1_change, p2_change = calculate_match_rating_changes(
            1200, 1000,
            winner_id=1,
            p1_id=1, p2_id=2
        )

        # Сильный получает мало
        assert p1_change < 16
        # Слабый теряет мало
        assert -16 < p2_change < 0

    def test_skill_gap_upset(self):
        """Слабый (1000) выигрывает у сильного (1200) - upset!"""
        p1_change, p2_change = calculate_match_rating_changes(
            1000, 1200,
            winner_id=1,
            p1_id=1, p2_id=2
        )

        # Слабый получает много
        assert p1_change > 20
        # Сильный теряет много
        assert p2_change < -20

    def test_extreme_rating_difference(self):
        """Экстремальная разница (2000 vs 800)."""
        p1_change, p2_change = calculate_match_rating_changes(
            2000, 800,
            winner_id=1,
            p1_id=1, p2_id=2
        )

        # Master выигрывает - expected score capped at 0.999
        # K × (1 - 0.999) = 32 × 0.001 = 0.032 → rounds to 0
        assert 0 <= p1_change <= 1, f"Master should gain ~0, got {p1_change}"
        # Novice теряет - expected score capped at 0.001
        # K × (0 - 0.001) = 32 × -0.001 = -0.032 → rounds to 0
        assert -1 <= p2_change <= 0, f"Novice should lose ~0, got {p2_change}"

    def test_zero_sum_property(self):
        """ELO система должна быть zero-sum (в среднем)."""
        scenarios = [
            (1000, 1000, 1),  # P1 wins
            (1200, 1000, 2),  # P2 (weak) wins (upset)
            (2000, 800, 1),   # P1 (master) wins
            (900, 1100, None),  # Draw
        ]

        for r1, r2, winner in scenarios:
            p1_change, p2_change = calculate_match_rating_changes(
                r1, r2,
                winner_id=winner,
                p1_id=1, p2_id=2
            )
            total = p1_change + p2_change
            # Может быть ±1 из-за rounding
            assert abs(total) <= 1, f"Total change should be ~0, got {total}"


class TestIntegration:
    """Интеграционные тесты."""

    def test_rating_progression(self):
        """Прогрессия рейтинга: слабый игрок побеждает много раз."""
        rating = 1000
        opponent_rating = 1000

        for _ in range(10):
            change, _ = calculate_match_rating_changes(
                rating, opponent_rating,
                winner_id=1,
                p1_id=1, p2_id=2
            )
            rating = apply_rating_bounds(rating + change)

        # После 10 побед должен вырасти
        assert rating > 1100, f"Rating should grow, got {rating}"

    def test_rating_floor(self):
        """Рейтинг не может упасть ниже 100."""
        rating = 100
        opponent_rating = 2000

        # Теряет несколько раз подряд
        for _ in range(20):
            change, _ = calculate_match_rating_changes(
                rating, opponent_rating,
                winner_id=2,
                p1_id=1, p2_id=2
            )
            rating = apply_rating_bounds(rating + change)

        assert rating >= 100, f"Rating should not go below 100, got {rating}"
