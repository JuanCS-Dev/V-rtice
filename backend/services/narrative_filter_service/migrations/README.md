# Database Migrations - Narrative Filter Service

## Schema Overview

### Tables

1. **semantic_representations** - Camada 1 (Semantic Processor)
   - Stores semantic representations of agent messages
   - Embeddings (384 dims float array)
   - Intent classification + confidence
   - Indexes: agent_id+timestamp, message_id

2. **strategic_patterns** - Camada 2 (Strategic Detector)
   - Game theory patterns (ALLIANCE, DECEPTION, INCONSISTENCY, COLLUSION)
   - Scores: mutual_information, deception_score, inconsistency_score
   - JSONB metadata for extensibility
   - Index: pattern_type+timestamp

3. **alliances** - Camada 2 (Strategic Detector)
   - Agent-to-agent alliances
   - Strength tracking (0.0-1.0)
   - Status: ACTIVE/DISSOLVED
   - Unique constraint: (agent_a, agent_b)

4. **verdicts** - Camada 3 (Verdict Synthesizer)
   - Final verdicts with auto-severity
   - Color coding (hex)
   - C2L recommendations
   - Evidence chain (message_ids array)
   - Index: status+severity+timestamp

## Usage

```bash
# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current version
alembic current

# Show migration history
alembic history
```

## Extensions

- **pgvector**: Required for embedding similarity search (future enhancement)

## Compliance

✅ Zero nullable fields without defaults
✅ All timestamps timezone-aware (TIMESTAMPTZ)
✅ Proper indexing for query patterns
✅ Unique constraints where needed
✅ JSONB for flexible metadata
