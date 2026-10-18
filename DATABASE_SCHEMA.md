# VoiceOS SQLite Persistence & Database Schema

## 1. Overview
VoiceOS stores all interaction sessions, agent turns, tool invocations, vocabulary definitions, and productivity analytics in a local SQLite database (`voiceos.db`). The database is configured with **Write-Ahead Logging (WAL)** mode for concurrency and zero lock contention between background audio threads and the UI.

---

## 2. Table Specifications

### 2.1 `voice_sessions`
Stores metadata and aggregated content for all voice and text interactions.
```sql
CREATE TABLE IF NOT EXISTS voice_sessions (
    id TEXT PRIMARY KEY,
    transcript TEXT,
    generated_text TEXT,
    app_name TEXT,
    window_title TEXT,
    duration_seconds REAL,
    word_count INTEGER,
    mode INTEGER DEFAULT 0,
    chat_history TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 2.2 `agent_turns`
Maintains individual conversational turns within an agent session.
```sql
CREATE TABLE IF NOT EXISTS agent_turns (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    sequence INTEGER DEFAULT 0,
    user_message TEXT,
    assistant_response TEXT,
    duration_ms INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES voice_sessions (id) ON DELETE CASCADE
);
```

### 2.3 `agent_tool_calls`
Records tool execution history (weather, calculations, system diagnostics).
```sql
CREATE TABLE IF NOT EXISTS agent_tool_calls (
    id TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    status TEXT,
    input_json TEXT,
    output_summary TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (turn_id) REFERENCES agent_turns (id) ON DELETE CASCADE
);
```

### 2.4 `dictionary`
User-defined custom vocabulary and pronunciation rules.
```sql
CREATE TABLE IF NOT EXISTS dictionary (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL UNIQUE,
    description TEXT,
    auto_added INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 2.5 `voice_session_insights`
Quantifies time saved, words dictated, and tool runs.
```sql
CREATE TABLE IF NOT EXISTS voice_session_insights (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    time_saved_seconds REAL DEFAULT 0,
    words INTEGER DEFAULT 0,
    duration_seconds REAL DEFAULT 0,
    prompts INTEGER DEFAULT 1,
    tool_runs INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
```

---

## 3. Query Patterns & Indexes
- Sessions are retrieved chronologically using `SELECT * FROM voice_sessions ORDER BY created_at DESC LIMIT ? OFFSET ?`.
- Real-time search in `HistoryDrawer` executes indexed scans on `transcript` and `generated_text`.
- Foreign key constraints with `ON DELETE CASCADE` ensure child records are cleanly purged upon session deletion.
