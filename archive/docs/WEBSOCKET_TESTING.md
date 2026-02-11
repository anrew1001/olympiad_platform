# WebSocket PvP Testing Guide

## Quick Start

### Prerequisites
- Running PostgreSQL
- FastAPI server running: `uvicorn app.main:app --reload`
- Two user accounts created

### Setup Test Users

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "email": "player1@test.com",
    "password": "password123"
  }'

curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player2",
    "email": "player2@test.com",
    "password": "password123"
  }'
```

### Get JWT Tokens

```bash
# Player 1
TOKEN1=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "player1@test.com", "password": "password123"}' | jq -r .access_token)

# Player 2
TOKEN2=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "player2@test.com", "password": "password123"}' | jq -r .access_token)
```

### Create Match

```bash
# Player 1 searches for match
curl -X POST http://localhost:8000/api/pvp/find \
  -H "Authorization: Bearer $TOKEN1"

# Player 2 joins match
RESPONSE=$(curl -X POST http://localhost:8000/api/pvp/find \
  -H "Authorization: Bearer $TOKEN2")

MATCH_ID=$(echo $RESPONSE | jq -r .match_id)
echo "Match ID: $MATCH_ID"
```

## Testing with websocat

Install websocat:
```bash
# macOS
brew install websocat

# Linux
cargo install websocat
```

### Terminal 1 - Player 1

```bash
websocat "ws://localhost:8000/api/pvp/ws/$MATCH_ID?token=$TOKEN1"
```

Expected output:
```json
{"type": "match_start", "tasks": [...]}
```

### Terminal 2 - Player 2

```bash
websocat "ws://localhost:8000/api/pvp/ws/$MATCH_ID?token=$TOKEN2"
```

Expected output:
```json
{"type": "match_start", "tasks": [...]}
```

### Submit Answers

In **Terminal 1** (Player 1), send a correct answer:

```json
{"type": "submit_answer", "task_id": 15, "answer": "x = 2"}
```

Expected response:
```json
{"type": "answer_result", "task_id": 15, "is_correct": true, "your_score": 1}
```

Player 2 should receive:
```json
{"type": "opponent_scored", "task_id": 15, "opponent_score": 1}
```

## Testing with JavaScript (Browser Console)

```javascript
const token = "YOUR_JWT_TOKEN_HERE";
const matchId = 123;  // Your match ID

const ws = new WebSocket(
  `ws://localhost:8000/api/pvp/ws/${matchId}?token=${token}`
);

ws.onopen = () => {
  console.log("Connected!");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);

  // Auto-respond to ping
  if (data.type === "ping") {
    ws.send(JSON.stringify({
      type: "pong",
      timestamp: data.timestamp
    }));
  }
};

ws.onerror = (error) => {
  console.error("Error:", error);
};

ws.onclose = () => {
  console.log("Disconnected");
};

// Submit an answer
function submitAnswer(taskId, answer) {
  ws.send(JSON.stringify({
    type: "submit_answer",
    task_id: taskId,
    answer: answer
  }));
}

// Example
submitAnswer(15, "x = 2");
```

## Scenario: Full Match Flow

1. **Player 1 connects** → Receives match_start with 5 tasks
2. **Player 2 connects** → Also receives match_start
3. **Player 1 answers task 1 correctly** → +1 score
4. **Player 2 sees opponent_scored** → Knows P1 got it
5. **Both answer all 5 tasks** → Match ends with match_end event
6. **Rating updates applied** → Winners +15, losers -5

## Event Types Reference

### Server → Client

| Event | Description |
|-------|-------------|
| `player_joined` | Opponent connected |
| `match_start` | Both online, match begins (5 tasks) |
| `answer_result` | Your answer result (is_correct, score) |
| `opponent_scored` | Opponent answered correctly |
| `match_end` | Match finished (winner, rating changes) |
| `opponent_disconnected` | Opponent left |
| `error` | Error processing message |
| `ping` | Heartbeat from server |

### Client → Server

| Event | Description |
|-------|-------------|
| `submit_answer` | Send answer to task |
| `pong` | Respond to heartbeat |

## Troubleshooting

### "User not found"
- JWT token is invalid or expired
- Re-login and get fresh token

### "Match not found"
- Match ID is wrong
- Match was deleted or cancelled

### "User not a participant"
- You're trying to join match you're not in
- Use correct match ID from /api/pvp/find response

### "FOR UPDATE cannot be applied..."
- Server issue with database locking
- Check that Match relationships are loaded with noload()

### Connection times out
- WebSocket heartbeat timeout (no pong received)
- Client should respond to ping with pong
- Browser console: `ws.send(JSON.stringify({type: "pong", timestamp: ...}))`

## Performance Notes

- **Message latency**: ~50-100ms locally
- **Database**: Per-message session (no connection pooling issues)
- **Heartbeat**: 30 second interval, 30 second timeout
- **Rating calculation**: O(1) operation
- **Score calculation**: COUNT query on MatchAnswer (indexed)

## Next Steps

- [ ] Add rate limiting (max 1 submit/sec)
- [ ] Implement reconnection support
- [ ] Add spectator mode
- [ ] Add replay system
- [ ] Performance profiling under load

## Files Reference

- `app/websocket/manager.py` - Connection management
- `app/websocket/pvp.py` - WebSocket endpoint
- `app/services/match_logic.py` - Answer processing
- `app/schemas/websocket.py` - Event schemas
