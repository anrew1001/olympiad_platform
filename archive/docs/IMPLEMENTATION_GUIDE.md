# ELO Rating & PvP Enhancement Implementation Guide

## 🎯 Project Overview

Implementing a production-ready ELO rating system with disconnect timeout handling, rate limiting, anti-cheat detection, and rating history tracking for the PvP tournament platform.

---

## ✅ Completed (Phases 1-3)

### Phase 1: ELO Calculation Service ✓
**File**: `backend/app/services/elo.py` (~200 lines)

**Key Functions**:
- `calculate_expected_score(rating_a, rating_b)` - Classical ELO expected score formula
- `calculate_rating_change(player_rating, opponent_rating, outcome, k_factor=32)` - Rating delta calculation
- `calculate_match_rating_changes(p1_rating, p2_rating, winner_id, p1_id, p2_id)` - Bilateral calculation
- `apply_rating_bounds(rating)` - Ensures rating >= 100

**Features**:
- Float calculations for precision, integer rounding for storage
- Edge case handling (extreme rating differences, overflow prevention)
- K-factor = 32 for all players (adaptive K infrastructure ready for Phase 2)
- Rating bounds: Min=100, No maximum (organic growth)

**Test Cases Included**:
- Equal ratings draw/win scenarios
- Strong beats weak (expected small gains)
- Upset victories (expected large gains)
- Extreme rating differences (100 vs 2800)

---

### Phase 2: Enhanced Match Logic ✓
**File**: `backend/app/services/match_logic.py` (updated)

**Updated Functions**:
1. **`finalize_match(match_id, session, reason="completion", winner_id=None)`**
   - IDEMPOTENCY: If already FINISHED, returns cached result without re-updating ratings
   - Reasons: "completion" | "forfeit" | "technical_error"
   - Technical error → status=ERROR, rating_change=0, no rating updates
   - Completion → normal ELO calculation
   - Forfeit → winner specified, loser forfeits

2. **`finalize_match_forfeit(match_id, user_id_disconnected, session)`**
   - Called when 30-second timeout expires
   - Remaining player wins, forfeited player loses
   - Full ELO calculation applied

3. **`handle_technical_error(match_id, session, error_message)`**
   - Used when both players disconnect simultaneously
   - Sets status=ERROR, no rating changes
   - Logs error for admin review

**Features**:
- ELO replaces fixed rating system (+15/-5/0)
- Uses `SELECT FOR UPDATE` with `noload()` for thread safety
- Applies rating bounds after ELO calculation
- Comprehensive logging for debugging

---

### Phase 3: Session Tracking in ConnectionManager ✓
**File**: `backend/app/websocket/manager.py` (updated)

**New Data Structures**:
```python
self._sessions: Dict[int, Dict[int, dict]]  # {match_id: {user_id: {'session_id': str, 'disconnect_task': Task|None}}}
self._rate_limits: Dict[int, Dict[int, dict]]  # {match_id: {user_id: {'last_answer_time': float}}}
```

**New Methods**:

1. **`connect_with_session(match_id, user_id, websocket, session_id) → bool`**
   - Returns `True` if reconnection (session exists with cancel-able timeout)
   - Returns `False` if new connection
   - Cancels disconnect_task on reconnection
   - Stores session metadata for tracking

2. **`cancel_disconnect_timer(match_id, user_id) → bool`**
   - Cancels pending 30-second timeout task
   - Called on successful reconnection

3. **`start_disconnect_timer(match_id, user_id, timeout_seconds, callback)`**
   - Starts async timeout using `asyncio.sleep()`
   - Calls callback if timeout expires (forfeit logic)
   - Creates background task stored in _sessions

4. **`check_rate_limit(match_id, user_id) → tuple[bool, float]`**
   - Enforces max 1 answer per second per user
   - Returns (is_allowed, wait_time_remaining)
   - Fast in-memory checks, no database queries

5. **`reset_rate_limit(match_id, user_id)`**
   - Clears rate limit on match end or disconnect

**Features**:
- Per-match locks for thread safety
- Auto-cleanup when match rooms empty
- 256-bit entropy session IDs (future: can integrate with Redis)

---

## 🚀 Remaining Implementation (Phases 4-8)

### Phase 4: WebSocket Endpoint Updates
**File**: `backend/app/websocket/pvp.py`

**Changes Required**:

1. **Add constants**:
```python
DISCONNECT_TIMEOUT = 30  # seconds for reconnection window
```

2. **Update imports**:
```python
from app.services.match_logic import (
    process_answer,
    check_match_completion,
    finalize_match,
    finalize_match_forfeit,  # NEW
    handle_technical_error,  # NEW
)
from app.services.anti_cheat import (  # NEW for Phase 7
    analyze_answer_timing,
    flag_suspicious_behavior,
)
import secrets  # for session_id generation
```

3. **Update connection flow** (lines ~454-460):
```python
# Generate session_id
session_id = secrets.token_urlsafe(32)

# Connect with session tracking
is_reconnection = await manager.connect_with_session(
    match_id, user.id, websocket, session_id
)

if is_reconnection:
    # Send reconnection_success event with current scores
    # Notify opponent
    pass
```

4. **Update disconnect handling** (lines ~525-559):
```python
except WebSocketDisconnect:
    logger.info(f"User {user.id if user else 'unknown'} disconnected from match {match_id}")

finally:
    if heartbeat:
        heartbeat.cancel()

    if user:
        # Check if opponent still connected
        opponent_id = manager.get_opponent_id(match_id, user.id)
        if opponent_id and manager.is_connected(match_id, opponent_id):
            # Start 30-second disconnect timer
            await manager.start_disconnect_timer(
                match_id, user.id, DISCONNECT_TIMEOUT,
                callback=lambda: handle_disconnect_timeout(match_id, user.id)
            )
            # Notify opponent with timeout info
            await manager.send_personal(
                match_id, opponent_id,
                OpponentDisconnectedEvent(
                    reconnecting=True,
                    timeout_seconds=30
                ).model_dump()
            )
        else:
            # Both disconnected - technical error
            async with async_session_maker() as session:
                await handle_technical_error(
                    match_id, session,
                    "Both players disconnected"
                )

        await manager.disconnect(match_id, user.id)
```

5. **Add timeout callback function**:
```python
async def handle_disconnect_timeout(match_id: int, user_id: int):
    """Called when 30-second timeout expires without reconnection"""
    async with async_session_maker() as session:
        try:
            # Verify still disconnected
            if manager.is_connected(match_id, user_id):
                return

            # Finalize as forfeit
            result_data = await finalize_match_forfeit(
                match_id, user_id, session
            )
            await session.commit()

            # Send match_end to remaining player
            opponent_id = manager.get_opponent_id(match_id, user_id)
            if opponent_id:
                await manager.send_personal(
                    match_id, opponent_id,
                    MatchEndEvent(
                        reason="forfeit",
                        winner_id=result_data["winner_id"],
                        ...
                    ).model_dump()
                )

            # Cleanup
            await manager.disconnect(match_id, user_id)
        except Exception as e:
            logger.error(f"Error in disconnect timeout: {e}")
```

6. **Update answer submission** (in `handle_message`, before line 256):
```python
# Check rate limit
is_allowed, wait_time = manager.check_rate_limit(match_id, user_id)
if not is_allowed:
    await manager.send_personal(
        match_id, user_id,
        ErrorEvent(
            message=f"Rate limited. Wait {wait_time:.1f}s",
            code="RATE_LIMITED"
        ).model_dump()
    )
    return

# Anti-cheat check (Phase 7)
is_suspicious, reason = await analyze_answer_timing(
    match_id, user_id, task_id, answer, session
)
if is_suspicious:
    await flag_suspicious_behavior(match_id, user_id, reason, session)
    logger.warning(f"Suspicious: Match {match_id}, User {user_id}: {reason}")
    # Still process answer to avoid false positives

# Process answer...
```

---

### Phase 5: Event Schema Updates
**File**: `backend/app/schemas/websocket.py`

**Changes**:

1. **Update OpponentDisconnectedEvent** (lines ~100-106):
```python
class OpponentDisconnectedEvent(BaseModel):
    type: str = Field("opponent_disconnected", description="Event type")
    timestamp: str = Field(..., description="ISO format timestamp")
    reconnecting: bool = Field(True, description="Can opponent reconnect?")
    timeout_seconds: Optional[int] = Field(None, description="Seconds until forfeit")
```

2. **Add OpponentReconnectedEvent**:
```python
class OpponentReconnectedEvent(BaseModel):
    type: str = Field("opponent_reconnected", description="Event type")
    timestamp: str = Field(..., description="ISO format timestamp")
```

3. **Add ReconnectionSuccessEvent**:
```python
class ReconnectionSuccessEvent(BaseModel):
    type: str = Field("reconnection_success", description="Event type")
    your_score: int = Field(..., description="Your current score")
    opponent_score: int = Field(..., description="Opponent's current score")
    time_elapsed: int = Field(..., description="Seconds since match start")
```

4. **Update MatchEndEvent** (lines ~89-98):
```python
class MatchEndEvent(BaseModel):
    type: str = Field("match_end", description="Event type")
    reason: str = Field(..., description="completion | forfeit | technical_error")
    winner_id: Optional[int] = Field(None, description="Winner ID or None for draw/error")
    # ... existing fields unchanged
```

**Backward Compatibility**: All new fields are optional with defaults, old clients continue to work.

---

## 🛡️ Anti-Cheat System (Phase 7) - DETAILED EXPLANATION

**File**: `backend/app/services/anti_cheat.py` (~300 lines)

### Architecture

The anti-cheat system uses **behavioral analysis** to detect suspicious play patterns without banning players outright. All flagged matches are logged for admin review.

### Core Detection Methods

#### 1. **Answer Timing Analysis** (`analyze_answer_timing`)

**What it detects**:
- Answers submitted before human reaction time (< 2 seconds after task shown)
- Answers submitted too fast for their length
- Burst patterns: >3 answers in < 5 seconds

**How it works**:
```python
async def analyze_answer_timing(
    match_id: int,
    user_id: int,
    task_id: int,
    answer: str,
    session: AsyncSession,
) -> tuple[bool, str | None]:
    """
    Check answer timing for suspicious patterns.

    Suspicion triggers:
    1. Time < MIN_ANSWER_TIME (2.0 seconds) → "instant_answer"
    2. Answer length > 50 chars AND time < 3s → "too_fast_for_length"
    3. Consecutive instant answers (threshold 3) → "answer_burst"
    """
```

**Min Answer Time Calculation**:
- `time_since_task_shown = now - task_load_time`
- If `time_since_task_shown < 2.0 seconds` → suspicious
- Rationale: Human reaction time is ~200ms minimum, reading + typing takes >2s for most

**Answer Burst Pattern**:
- Track last 5 answers per user in match
- If 3+ consecutive answers in < 5 seconds → flag "answer_burst"
- Signature of bot or auto-answer tools

#### 2. **Answer Pattern Analysis** (`analyze_answer_pattern`)

**What it detects**:
- 100% accuracy across all 5 tasks (statistically unlikely unless cheating)
- Identical timing patterns between answers (bot signature)
- Copy-paste answer detection

**How it works**:
```python
async def analyze_answer_pattern(
    match_id: int,
    user_id: int,
    session: AsyncSession,
) -> tuple[bool, str | None]:
    """
    Analyze match-wide answer patterns for cheating signatures.

    Suspicion triggers:
    1. All answers correct + answer_count == total_tasks → "perfect_accuracy"
       - Threshold: SUSPICIOUS_ACCURACY_THRESHOLD (0.95)
       - Combined with timing data

    2. All 5 answers have similar submission times (±500ms) → "identical_timing_pattern"
       - Suggests scripted/automated submission

    3. Answer text similarity > 90% with previous match → "copy_paste_answers"
       - Uses difflib.SequenceMatcher to compare answer texts
    """
```

**Pattern Examples**:
- User A: Answers [2.1s, 2.3s, 2.0s, 2.2s, 2.1s] → Regular human (±200ms variation)
- User B: Answers [0.5s, 0.6s, 0.5s, 0.6s, 0.5s] → Bot (constant <1s pattern)
- User C: All 5 tasks correct + timing <1s each → HIGH SUSPICION

#### 3. **Flagging & Logging** (`flag_suspicious_behavior`)

**What happens when suspicious activity is detected**:

1. **Log Entry Created**:
   - `match_id`: Which match
   - `user_id`: Which player
   - `reason`: "instant_answer" | "answer_burst" | "perfect_accuracy" | etc.
   - `details`: JSON with timing data, answer counts, patterns
   - `created_at`: Timestamp
   - `reviewed`: Initially FALSE (pending admin review)
   - `reviewer_id`: NULL until admin reviews
   - `action_taken`: NULL until admin decides (options: "warning", "ban", "false_positive")

2. **Database Schema**:
```sql
CREATE TABLE suspicious_activity (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    reason TEXT NOT NULL,  -- category of suspicious behavior
    details JSONB,  -- timing data, answer patterns, etc.
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    reviewed BOOLEAN DEFAULT FALSE,  -- admin review flag
    reviewer_id INTEGER REFERENCES users(id),  -- which admin reviewed
    action_taken TEXT,  -- "warning", "ban", "false_positive"
    INDEX: (user_id, created_at DESC), (match_id), (reviewed)
);
```

3. **Admin Dashboard Usage** (future):
```
GET /api/admin/suspicious-activity?reviewed=false
Shows all unreviewed flags

PUT /api/admin/suspicious-activity/{id}
Admin marks as reviewed and takes action

GET /api/users/{user_id}/suspicious-history
User's complete flag history for transparency
```

### Design Philosophy

**Why not instant ban?**
- False positives happen (lag, fast typers exist)
- Different difficulty tasks have different reaction times
- Admin must review context

**How to avoid false positives**:
- Multiple independent checks (all must trigger for high confidence)
- Timing checks combined with accuracy checks
- Burst pattern + instant answers together = higher suspicion than alone
- Probability model: P(cheating | flags) increases with more flags

**Example Risk Scoring** (pseudocode for admin):
```
risk_score = 0
if instant_answers: risk_score += 30
if answer_burst: risk_score += 25
if perfect_accuracy: risk_score += 25
if identical_timing: risk_score += 20

Score < 50: Probably innocent (gaming while tired, etc.)
Score 50-75: Suspicious, monitor account
Score > 75: High confidence cheating, consider warning
Score > 90: Recommend ban (multiple flags + patterns)
```

---

## 📊 Phase 6: Rate Limiting
**Implementation Location**: `backend/app/websocket/manager.py` (Already added in Phase 3!)

**Already implemented**:
- `check_rate_limit(match_id, user_id) → (is_allowed, wait_time)`
- `reset_rate_limit(match_id, user_id)`
- Integration point: Call in WebSocket handler before `process_answer()`

**Configuration**:
```python
ANSWER_RATE_LIMIT = 1.0  # seconds between answers
```

---

## 📈 Phase 8: Rating History

**Files to create**:
1. `backend/app/models/rating_history.py`
2. `backend/app/routers/rating_history.py`
3. Database migrations for 2 new tables

**Database Schema**:
```sql
CREATE TABLE rating_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    match_id INTEGER NOT NULL REFERENCES matches(id),
    old_rating INTEGER NOT NULL,
    new_rating INTEGER NOT NULL,
    rating_change INTEGER NOT NULL,
    opponent_id INTEGER NOT NULL REFERENCES users(id),
    opponent_rating INTEGER NOT NULL,
    outcome VARCHAR(15) NOT NULL,  -- "win", "loss", "draw", "forfeit_win", "forfeit_loss"
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    INDEX: (user_id, created_at DESC), (match_id)
);

CREATE TABLE suspicious_activity (
    -- See anti-cheat schema above
);
```

**API Endpoints**:
```
GET /api/users/{user_id}/rating-history?limit=50&offset=0
→ Returns: [{match_id, opponent, outcome, rating_change, created_at}]

GET /api/users/{user_id}/rating-graph?days=30
→ Returns: Time-series {date: "2026-02-06", rating: 1150}
```

**Integration in `finalize_match()`**:
```python
# After updating User.rating:
history_entries = [
    RatingHistory(
        user_id=player1.id,
        match_id=match_id,
        old_rating=old_rating_p1,
        new_rating=player1.rating,
        rating_change=p1_change,
        opponent_id=player2.id,
        opponent_rating=old_rating_p2,
        outcome=determine_outcome(winner_id, player1.id, reason),
        created_at=datetime.utcnow()
    ),
    # ... similar for player2
]
session.add_all(history_entries)
```

---

## 🧪 Testing Strategy

### Unit Tests
- **`tests/services/test_elo.py`**: ELO calculations, edge cases
- **`tests/services/test_anti_cheat.py`**: Detection methods, false positives
- **`tests/websocket/test_manager.py`**: Session tracking, rate limiting

### Integration Tests
- **`tests/integration/test_pvp_elo.py`**: Full match with ELO updates
- **`tests/integration/test_pvp_disconnect.py`**: Disconnect → reconnect → forfeit
- **`tests/integration/test_anti_cheat_detection.py`**: Trigger suspicious patterns

### Manual Testing Checklist
```
✓ Normal match completion → ELO updated correctly
✓ Disconnect 15s → Reconnect → Match continues
✓ Disconnect 35s → Timeout → Match forfeited
✓ Both disconnect → Status=ERROR, ratings unchanged
✓ Answer rate limit: 2 answers/sec → 2nd rejected
✓ Anti-cheat: 0.5s answers → Flagged as suspicious
✓ Rating history: Query shows all past matches
✓ Admin suspicious activity: View flagged matches
```

---

## 🔧 Quick Migration Commands

```bash
# Create migrations
alembic revision --autogenerate -m "Add rating_history table"
alembic revision --autogenerate -m "Add suspicious_activity table"

# Apply migrations
alembic upgrade head

# Test ELO service
cd backend && python -c "from app.services.elo import simulate_match; print(simulate_match(1000, 1200, 'a'))"
```

---

## 📝 Configuration Summary

All constants defined in code (future: move to env vars/config file):

```python
# ELO System (backend/app/services/elo.py)
K_FACTOR = 32
MIN_RATING = 100
MAX_RATING_DIFF = 800

# WebSocket (backend/app/websocket/pvp.py)
DISCONNECT_TIMEOUT = 30
HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 30

# Rate Limiting (backend/app/websocket/manager.py)
ANSWER_RATE_LIMIT = 1.0  # seconds

# Anti-Cheat (backend/app/services/anti_cheat.py)
MIN_ANSWER_TIME = 2.0  # seconds (human reaction time)
INSTANT_ANSWER_THRESHOLD = 3  # answers in <5s = burst
SUSPICIOUS_ACCURACY_THRESHOLD = 0.95  # >95% = suspicious
```

---

## 📚 File Summary

### Created Files
- ✓ `backend/app/services/elo.py` (200 lines)
- ⏳ `backend/app/services/anti_cheat.py` (300 lines) - Phase 7
- ⏳ `backend/app/models/rating_history.py` (50 lines) - Phase 8
- ⏳ `backend/app/models/suspicious_activity.py` (50 lines) - Phase 7/8
- ⏳ `backend/app/routers/rating_history.py` (150 lines) - Phase 8

### Modified Files
- ✓ `backend/app/services/match_logic.py` (+180 lines)
- ✓ `backend/app/websocket/manager.py` (+150 lines)
- ⏳ `backend/app/websocket/pvp.py` (+180 lines) - Phase 4
- ⏳ `backend/app/schemas/websocket.py` (+40 lines) - Phase 5
- ⏳ `backend/app/main.py` (+3 lines) - Include rating_history router

### Database Migrations
- ⏳ `add_rating_history_table.py` - Phase 8
- ⏳ `add_suspicious_activity_table.py` - Phase 7

---

## 🎯 Implementation Order

1. ✓ Phase 1-3: Core services & session tracking
2. ⏳ Phase 4: WebSocket endpoint (critical for runtime)
3. ⏳ Phase 5: Event schemas (required by Phase 4)
4. ⏳ Phase 6: Rate limiting (mostly done, integration in Phase 4)
5. ⏳ Phase 7: Anti-cheat detection (optional but recommended)
6. ⏳ Phase 8: Rating history (frontend nice-to-have)
7. ⏳ Testing & verification
