"""
Infrastructure Smoke Tests
Validates that Testcontainers setup is working correctly

Author: Claude Code + JuanCS-Dev
Date: 2025-10-20
"""

import pytest
import time


class TestTestcontainersInfrastructure:
    """Smoke tests for Testcontainers infrastructure."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_kafka_container_health(self, kafka_container, kafka_admin):
        """
        SCENARIO: Kafka container is running and accessible
        EXPECTED: Can connect and list topics
        """
        # Act - list topics (should not raise exception)
        topics = kafka_admin.list_topics()

        # Assert
        assert topics is not None
        bootstrap = kafka_container.get_bootstrap_server()
        assert "localhost" in bootstrap or "0.0.0.0" in bootstrap

    @pytest.mark.integration
    def test_kafka_producer_consumer_flow(self, kafka_producer, kafka_container):
        """
        SCENARIO: Can produce and consume messages from Kafka
        EXPECTED: Message sent = message received
        """
        from kafka import KafkaConsumer

        topic_name = "test_topic_smoke"

        # Arrange
        test_message = b"Hello from MAXIMUS test suite"

        # Act - Produce
        future = kafka_producer.send(topic_name, value=test_message)
        kafka_producer.flush()
        record_metadata = future.get(timeout=10)

        # Act - Consume
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000
        )

        messages = []
        for message in consumer:
            messages.append(message.value)
            break  # Get first message only

        consumer.close()

        # Assert
        assert record_metadata.topic == topic_name
        assert len(messages) == 1
        assert test_message in messages[0]

    @pytest.mark.integration
    def test_consciousness_topics_created(self, consciousness_topics):
        """
        SCENARIO: Consciousness topics are pre-created
        EXPECTED: All 5 topics exist
        """
        # Assert
        assert len(consciousness_topics) == 5
        assert "consciousness.global_workspace" in consciousness_topics
        assert "consciousness.visual_cortex" in consciousness_topics
        assert "consciousness.thalamus" in consciousness_topics
        assert "consciousness.prefrontal" in consciousness_topics
        assert "consciousness.neuromodulation" in consciousness_topics

    @pytest.mark.integration
    def test_redis_container_health(self, redis_client_fixture):
        """
        SCENARIO: Redis container is running and accessible
        EXPECTED: Can ping and set/get keys
        """
        # Act & Assert - Ping
        assert redis_client_fixture.ping() is True

        # Act - Set and get
        redis_client_fixture.set("test_key", "test_value")
        value = redis_client_fixture.get("test_key")

        # Assert
        assert value == "test_value"

    @pytest.mark.integration
    def test_redis_streams_functionality(self, redis_client_fixture):
        """
        SCENARIO: Redis Streams work for consciousness hot-path
        EXPECTED: Can add and read from stream
        """
        stream_name = "consciousness:test_stream"

        # Act - Add to stream
        message_id = redis_client_fixture.xadd(
            stream_name,
            {"event": "visual_input", "data": "[1,2,3]"}
        )

        # Act - Read from stream
        messages = redis_client_fixture.xread({stream_name: 0}, count=1)

        # Assert
        assert message_id is not None
        assert len(messages) == 1
        assert messages[0][0] == stream_name
        assert len(messages[0][1]) > 0

        # Cleanup
        redis_client_fixture.delete(stream_name)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_postgres_container_health(self, postgres_connection):
        """
        SCENARIO: PostgreSQL container is running
        EXPECTED: Can execute queries
        """
        # Act
        cursor = postgres_connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()

        # Assert
        assert version is not None
        assert "PostgreSQL" in version[0]

    @pytest.mark.integration
    def test_postgres_governance_schema(self, postgres_connection):
        """
        SCENARIO: Governance schema is initialized
        EXPECTED: Tables exist with sample data
        """
        cursor = postgres_connection.cursor()

        # Check schema exists
        cursor.execute("""
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name = 'governance'
        """)
        schema = cursor.fetchone()
        assert schema is not None

        # Check tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'governance'
            AND table_name = 'audit_trail'
        """)
        table = cursor.fetchone()
        assert table is not None

        # Check precedents table has sample data
        cursor.execute("SELECT COUNT(*) FROM governance.precedents")
        count = cursor.fetchone()[0]
        assert count >= 3  # We inserted 3 sample records

        cursor.close()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_minio_container_health(self, minio_container):
        """
        SCENARIO: MinIO container is running
        EXPECTED: Container is accessible
        """
        # Assert - Container is running
        assert minio_container.get_container_host_ip() is not None
        port = minio_container.get_exposed_port(9000)
        assert port is not None

    @pytest.mark.integration
    def test_full_stack_integration(
        self,
        kafka_producer,
        redis_client_fixture,
        postgres_connection,
        consciousness_topics
    ):
        """
        SCENARIO: All services work together in integration
        EXPECTED: Can simulate consciousness flow through entire stack
        """
        # Simulate consciousness flow:
        # 1. Visual input via Kafka
        # 2. State in Redis
        # 3. Audit in PostgreSQL

        # Step 1: Kafka message
        visual_input = {
            "timestamp": time.time(),
            "type": "visual_cortex",
            "data": [0.1, 0.2, 0.3]
        }

        kafka_producer.send("consciousness.visual_cortex", value=str(visual_input))
        kafka_producer.flush()

        # Step 2: Redis state
        state_key = "consciousness:visual:state"
        redis_client_fixture.set(state_key, "active")
        redis_client_fixture.expire(state_key, 60)

        state = redis_client_fixture.get(state_key)
        assert state == "active"

        # Step 3: PostgreSQL audit
        cursor = postgres_connection.cursor()
        cursor.execute("""
            INSERT INTO governance.audit_trail (action_type, actor, context)
            VALUES (%s, %s, %s)
        """, ("consciousness_event", "visual_cortex", '{"event": "processed"}'))

        cursor.execute("""
            SELECT COUNT(*) FROM governance.audit_trail
            WHERE action_type = 'consciousness_event'
        """)
        count = cursor.fetchone()[0]
        cursor.close()

        # Assert - All steps succeeded
        assert count >= 1

        print("✅ Full stack integration test passed!")
        print("   - Kafka: Message sent")
        print("   - Redis: State stored")
        print("   - PostgreSQL: Audit logged")
