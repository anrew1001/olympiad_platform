"""
ELO Rating System Service

Implements classical ELO formula for calculating player rating changes
based on match outcomes.

Formula:
  E_a = 1 / (1 + 10^((R_b - R_a) / 400))
  ΔR = K × (S - E_a)

Where:
  R_a, R_b = player ratings
  E_a = expected score for player A
  S = actual result (1.0=win, 0.5=draw, 0.0=loss)
  K = rating volatility factor (32 for standard play)
"""

import logging
import math

logger = logging.getLogger(__name__)

# Configuration Constants
K_FACTOR = 32  # Standard K-factor for established players
MIN_RATING = 100  # Minimum allowed rating (prevent negative)
MAX_RATING_DIFF = 800  # Beyond this, expected score is capped at 0.999/0.001


def calculate_expected_score(rating_a: int, rating_b: int) -> float:
    """
    Calculate expected score for player A against player B.

    Uses the classical ELO formula:
    E_a = 1 / (1 + 10^((R_b - R_a) / 400))

    Edge cases:
    - Extreme rating differences (>800): naturally approaches 0 or 1
    - Very close ratings: expected score approaches 0.5

    Args:
        rating_a: Rating of player A
        rating_b: Rating of player B

    Returns:
        Expected score (0.0 to 1.0), where 1.0 = guaranteed win, 0.0 = guaranteed loss
    """
    # Calculate the exponent safely, handling extreme differences
    rating_diff = rating_b - rating_a
    exponent = rating_diff / 400.0

    # Prevent overflow in 10^x calculation by capping exponent
    # 10^50 is already 1e50, so cap at reasonable values
    if exponent > 10:
        return 0.001  # Extremely weak player
    elif exponent < -10:
        return 0.999  # Extremely strong player

    expected = 1.0 / (1.0 + (10.0 ** exponent))
    return expected


def calculate_rating_change(
    player_rating: int,
    opponent_rating: int,
    outcome: float,
    k_factor: int = K_FACTOR,
) -> int:
    """
    Calculate rating change for a player based on match outcome.

    Formula:
    ΔR = K × (S - E_a)

    Where:
    - K = rating volatility (32 for standard)
    - S = actual result (1.0=win, 0.5=draw, 0.0=loss)
    - E_a = expected score (0.0 to 1.0)

    Args:
        player_rating: Current rating of the player
        opponent_rating: Current rating of the opponent
        outcome: Match outcome from player's perspective
                 1.0 = decisive win
                 0.5 = draw
                 0.0 = decisive loss
        k_factor: Rating volatility (default 32)

    Returns:
        Rating change (can be negative), rounded to nearest integer
    """
    if not (0.0 <= outcome <= 1.0):
        raise ValueError(f"Outcome must be between 0.0 and 1.0, got {outcome}")

    expected_score = calculate_expected_score(player_rating, opponent_rating)
    rating_change = k_factor * (outcome - expected_score)

    # Round to nearest integer for database storage
    return round(rating_change)


def calculate_match_rating_changes(
    p1_rating: int,
    p2_rating: int,
    winner_id: int | None,
    p1_id: int,
    p2_id: int,
) -> tuple[int, int]:
    """
    Calculate rating changes for both players in a match.

    Determines the outcome (win/loss/draw) for each player and calculates
    their respective rating changes using the ELO formula.

    Args:
        p1_rating: Current rating of player 1
        p2_rating: Current rating of player 2
        winner_id: ID of winner (None if draw)
        p1_id: ID of player 1
        p2_id: ID of player 2

    Returns:
        Tuple of (player1_change, player2_change)
        Both are integers that can be positive or negative
    """
    if winner_id is None:
        # Draw: both players get 0.5 expected result
        p1_outcome = 0.5
        p2_outcome = 0.5
    elif winner_id == p1_id:
        # Player 1 wins: 1.0 for winner, 0.0 for loser
        p1_outcome = 1.0
        p2_outcome = 0.0
    elif winner_id == p2_id:
        # Player 2 wins: 0.0 for loser, 1.0 for winner
        p1_outcome = 0.0
        p2_outcome = 1.0
    else:
        raise ValueError(f"winner_id {winner_id} is neither player 1 ({p1_id}) nor player 2 ({p2_id})")

    # Calculate changes
    p1_change = calculate_rating_change(p1_rating, p2_rating, p1_outcome)
    p2_change = calculate_rating_change(p2_rating, p1_rating, p2_outcome)

    # Apply minimum rating constraint (prevent going below MIN_RATING)
    # Note: We allow the change to be negative, but will enforce minimum in database update
    return p1_change, p2_change


def get_k_factor(rating: int, num_games: int | None = None) -> int:
    """
    Get K-factor for a player based on rating and experience.

    Current implementation: Returns fixed K=32 for all players.

    Future enhancements (Phase 2+):
    - K=40 for provisional players (< 30 games)
    - K=32 for established players (1200-2000)
    - K=24 for expert players (2000+)
    - K=16 for elite players (2400+)

    Args:
        rating: Player's current rating
        num_games: Number of games played (for provisional rating logic)

    Returns:
        K-factor to use for rating calculations
    """
    # Phase 1: Fixed K-factor for all players
    return K_FACTOR


def apply_rating_bounds(rating: int) -> int:
    """
    Apply bounds to ensure rating stays within valid range.

    Enforces:
    - Minimum rating: MIN_RATING (100)
    - Maximum rating: No limit (organic growth)

    Args:
        rating: Raw rating value

    Returns:
        Rating within valid bounds
    """
    return max(rating, MIN_RATING)


# Test/Debug functions

def simulate_match(rating_a: int, rating_b: int, winner: str = "a") -> dict:
    """
    Simulate a match and show rating change calculations.

    Useful for testing and understanding ELO behavior.

    Args:
        rating_a: Rating of player A
        rating_b: Rating of player B
        winner: "a" for A wins, "b" for B wins, "draw" for draw

    Returns:
        Dictionary with detailed ELO calculations
    """
    expected_a = calculate_expected_score(rating_a, rating_b)
    expected_b = calculate_expected_score(rating_b, rating_a)

    if winner == "a":
        outcome_a, outcome_b = 1.0, 0.0
        result_text = "Player A wins"
    elif winner == "b":
        outcome_a, outcome_b = 0.0, 1.0
        result_text = "Player B wins"
    elif winner == "draw":
        outcome_a, outcome_b = 0.5, 0.5
        result_text = "Draw"
    else:
        raise ValueError(f"winner must be 'a', 'b', or 'draw', got {winner}")

    change_a = calculate_rating_change(rating_a, rating_b, outcome_a)
    change_b = calculate_rating_change(rating_b, rating_a, outcome_b)

    return {
        "result": result_text,
        "player_a": {
            "rating_before": rating_a,
            "rating_after": rating_a + change_a,
            "change": change_a,
            "expected_score": round(expected_a, 4),
            "actual_score": outcome_a,
        },
        "player_b": {
            "rating_before": rating_b,
            "rating_after": rating_b + change_b,
            "change": change_b,
            "expected_score": round(expected_b, 4),
            "actual_score": outcome_b,
        },
    }
