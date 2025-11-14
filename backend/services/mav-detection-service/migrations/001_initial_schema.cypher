// ============================================================================
// MAV DETECTION SERVICE - NEO4J INITIAL SCHEMA
// ============================================================================
// Constitutional: Lei Zero - network analysis respects user privacy
//
// This migration creates the initial graph schema for detecting coordinated
// MAV (Militância em Ambientes Virtuais) campaigns on social media.
//
// Research-based patterns from 2025 studies on coordinated inauthentic behavior
// ============================================================================

// ============================================================================
// NODE CONSTRAINTS (Unique IDs)
// ============================================================================

CREATE CONSTRAINT campaign_id_unique IF NOT EXISTS
FOR (c:Campaign) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT account_id_unique IF NOT EXISTS
FOR (a:Account) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT post_id_unique IF NOT EXISTS
FOR (p:Post) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT hashtag_tag_unique IF NOT EXISTS
FOR (h:Hashtag) REQUIRE h.tag IS UNIQUE;

// ============================================================================
// INDEXES (Performance optimization for common queries)
// ============================================================================

// Campaign indexes
CREATE INDEX campaign_type_idx IF NOT EXISTS
FOR (c:Campaign) ON (c.type);

CREATE INDEX campaign_target_idx IF NOT EXISTS
FOR (c:Campaign) ON (c.target);

CREATE INDEX campaign_start_time_idx IF NOT EXISTS
FOR (c:Campaign) ON (c.start_time);

CREATE INDEX campaign_confidence_idx IF NOT EXISTS
FOR (c:Campaign) ON (c.confidence_score);

// Account indexes
CREATE INDEX account_platform_idx IF NOT EXISTS
FOR (a:Account) ON (a.platform);

CREATE INDEX account_creation_date_idx IF NOT EXISTS
FOR (a:Account) ON (a.creation_date);

CREATE INDEX account_username_idx IF NOT EXISTS
FOR (a:Account) ON (a.username);

// Post indexes
CREATE INDEX post_timestamp_idx IF NOT EXISTS
FOR (p:Post) ON (p.timestamp);

// Entity indexes
CREATE INDEX entity_name_idx IF NOT EXISTS
FOR (e:Entity) ON (e.name);

CREATE INDEX entity_type_idx IF NOT EXISTS
FOR (e:Entity) ON (e.type);

// ============================================================================
// RELATIONSHIP INDEXES
// ============================================================================

// Index on participation role
CREATE INDEX participates_role_idx IF NOT EXISTS
FOR ()-[r:PARTICIPATES_IN]-() ON (r.role);

// Index on post timing (for temporal coordination detection)
CREATE INDEX posted_timestamp_idx IF NOT EXISTS
FOR ()-[r:POSTED]-() ON (r.timestamp);

// ============================================================================
// EXAMPLE CAMPAIGN TYPES (For reference)
// ============================================================================
//
// Campaign types based on 2025 research:
// - coordinated_harassment: Targeted mass harassment campaigns
// - disinformation: Coordinated spread of false information
// - reputation_assassination: Organized attacks to destroy credibility
// - astroturfing: Fake grassroots movements
// - amplification: Artificial boosting of specific narratives
// - sock_puppet_network: Multiple fake accounts controlled by same entity
// - coordinated_reporting: Mass false reporting to silence targets
//
// ============================================================================

// ============================================================================
// GRAPH MODEL DOCUMENTATION
// ============================================================================
//
// NODES:
//
// (:Campaign)
//   - id: Unique campaign identifier (UUID)
//   - type: Campaign type (coordinated_harassment, disinformation, etc.)
//   - target: Primary target of the campaign (person, organization, topic)
//   - start_time: Campaign start timestamp (ISO 8601)
//   - end_time: Campaign end timestamp (optional)
//   - confidence_score: Detection confidence (0.0-1.0)
//   - status: Campaign status (active, monitored, resolved)
//   - metadata: Additional campaign data (JSONB)
//
// (:Account)
//   - id: Unique account identifier
//   - username: Account username/handle
//   - platform: Social media platform (twitter, telegram, etc.)
//   - creation_date: Account creation timestamp
//   - follower_count: Number of followers
//   - following_count: Number of following
//   - post_count: Total number of posts
//   - metadata: Additional account metrics (engagement rate, etc.)
//
// (:Post)
//   - id: Unique post identifier
//   - content: Post text content
//   - timestamp: Post creation time
//   - engagement_count: Total engagements (likes, shares, etc.)
//   - metadata: Additional post data (hashtags, mentions, media)
//
// (:Entity)
//   - id: Unique entity identifier
//   - name: Entity name (person, organization, topic)
//   - type: Entity type (person, organization, topic, location)
//   - metadata: Additional entity information
//
// (:Hashtag)
//   - tag: Hashtag text (without #)
//   - first_seen: First appearance timestamp
//   - total_usage_count: Total times used across all posts
//
// RELATIONSHIPS:
//
// (:Account)-[:PARTICIPATES_IN {role, detected_at}]->(:Campaign)
//   - role: Participation role (coordinator, amplifier, bot)
//   - detected_at: When participation was detected
//
// (:Account)-[:POSTED {timestamp}]->(:Post)
//   - timestamp: When the post was created
//
// (:Post)-[:PART_OF]->(:Campaign)
//   - Links posts to campaigns they belong to
//
// (:Post)-[:MENTIONS]->(:Entity)
//   - Links posts to entities they mention
//
// (:Post)-[:TAGGED_WITH]->(:Hashtag)
//   - Links posts to hashtags they contain
//
// (:Account)-[:FOLLOWS]->(:Account)
//   - Follower relationships between accounts
//
// (:Account)-[:SIMILAR_TO {similarity_score}]->(:Account)
//   - Accounts with similar behavior patterns
//   - similarity_score: Behavioral similarity (0.0-1.0)
//
// ============================================================================

// ============================================================================
// CONSTITUTIONAL COMPLIANCE ANNOTATIONS
// ============================================================================
//
// Lei Zero - Human Oversight:
// - High-confidence campaigns (>0.8) require human review
// - All account blocking actions logged for audit
// - False positive feedback mechanism implemented
//
// P4 - Rastreabilidade Total:
// - All graph mutations logged with timestamps
// - Campaign detection evidence preserved
// - Attribution trails maintained
//
// Privacy Protections:
// - Public social media data only (no private messages)
// - Anonymized analytics for general patterns
// - Data retention: 90 days for resolved campaigns
//
// ============================================================================

// ============================================================================
// MIGRATION COMPLETE
// ============================================================================
