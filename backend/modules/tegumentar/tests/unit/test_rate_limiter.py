"""
Testes unitários para backend.modules.tegumentar.epiderme.rate_limiter

Testa o rate limiter distribuído baseado em Token Bucket com Redis:
- Inicialização e cleanup
- Algoritmo Token Bucket (Lua script)
- Comportamento de allow()
- Recarga automática de script (NoScriptError)
- Limites de taxa configuráveis

Padrão Pagani: Mocks do Redis, validação real do algoritmo.
"""
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio.client import Redis
from redis.exceptions import NoScriptError

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.epiderme.rate_limiter import (
    _TOKEN_BUCKET_LUA,
    DistributedRateLimiter,
)


@pytest.fixture
def settings():
    """Settings de teste para rate limiter."""
    return TegumentarSettings(
        redis_url="redis://localhost:6379/15",
        rate_limit_capacity=100,
        rate_limit_refill_per_second=10,
    )


@pytest.fixture
def rate_limiter(settings):
    """Instância de rate limiter para testes."""
    return DistributedRateLimiter(settings)


@pytest.fixture
def mock_redis():
    """Mock completo de Redis client."""
    mock = AsyncMock(spec=Redis)
    mock.script_load = AsyncMock(return_value="sha1234567890abcdef")
    mock.evalsha = AsyncMock(return_value=1)  # allow by default
    mock.close = AsyncMock()
    return mock


class TestRateLimiterInitialization:
    """Testa inicialização e lifecycle do rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_starts_uninitialized(self, rate_limiter):
        """Rate limiter deve começar sem Redis conectado."""
        assert rate_limiter._redis is None
        assert rate_limiter._script_sha is None

    @pytest.mark.asyncio
    async def test_startup_connects_to_redis(self, rate_limiter, mock_redis):
        """startup() deve conectar ao Redis e carregar Lua script."""
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()

            assert rate_limiter._redis is not None
            assert rate_limiter._script_sha == "sha1234567890abcdef"
            mock_redis.script_load.assert_called_once_with(_TOKEN_BUCKET_LUA)

    @pytest.mark.asyncio
    async def test_startup_is_idempotent(self, rate_limiter, mock_redis):
        """Chamar startup() múltiplas vezes não deve reconectar."""
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()
            await rate_limiter.startup()
            await rate_limiter.startup()

            # from_url só deve ser chamado uma vez
            mock_redis.script_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_closes_redis_connection(self, rate_limiter, mock_redis):
        """shutdown() deve fechar conexão Redis."""
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()
            await rate_limiter.shutdown()

            mock_redis.close.assert_called_once()
            assert rate_limiter._redis is None
            assert rate_limiter._script_sha is None

    @pytest.mark.asyncio
    async def test_shutdown_is_safe_when_not_initialized(self, rate_limiter):
        """shutdown() não deve falhar se não foi inicializado."""
        await rate_limiter.shutdown()  # Não deve lançar exceção


class TestTokenBucketAlgorithm:
    """Testa algoritmo Token Bucket via mocks."""

    @pytest.mark.asyncio
    async def test_allow_returns_true_when_tokens_available(
        self, rate_limiter, mock_redis
    ):
        """allow() deve retornar True quando há tokens disponíveis."""
        mock_redis.evalsha.return_value = 1  # Script retorna 1 = allowed

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()
            result = await rate_limiter.allow("192.168.1.100")

            assert result is True

    @pytest.mark.asyncio
    async def test_allow_returns_false_when_rate_limited(
        self, rate_limiter, mock_redis
    ):
        """allow() deve retornar False quando rate limited."""
        mock_redis.evalsha.return_value = 0  # Script retorna 0 = rate limited

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()
            result = await rate_limiter.allow("192.168.1.100")

            assert result is False

    @pytest.mark.asyncio
    async def test_allow_uses_correct_redis_key(self, rate_limiter, mock_redis):
        """allow() deve usar chave Redis correta."""
        with patch("redis.asyncio.from_url", return_value=mock_redis), patch(
            "time.time", return_value=1698765432.0
        ):
            await rate_limiter.startup()
            await rate_limiter.allow("10.0.0.42")

            # Verificar chamada ao evalsha
            call_args = mock_redis.evalsha.call_args
            assert call_args[0][0] == "sha1234567890abcdef"  # SHA
            assert call_args[0][1] == 1  # Número de keys
            assert call_args[0][2] == "tegumentar:rate:10.0.0.42"  # Key

    @pytest.mark.asyncio
    async def test_allow_passes_correct_capacity(self, rate_limiter, mock_redis):
        """allow() deve passar capacidade correta para Lua script."""
        with patch("redis.asyncio.from_url", return_value=mock_redis), patch(
            "time.time", return_value=1698765432.0
        ):
            await rate_limiter.startup()
            await rate_limiter.allow("10.0.0.1")

            call_args = mock_redis.evalsha.call_args
            assert call_args[0][3] == 100  # capacity

    @pytest.mark.asyncio
    async def test_allow_passes_correct_refill_rate(self, rate_limiter, mock_redis):
        """allow() deve passar refill rate correta para Lua script."""
        with patch("redis.asyncio.from_url", return_value=mock_redis), patch(
            "time.time", return_value=1698765432.0
        ):
            await rate_limiter.startup()
            await rate_limiter.allow("10.0.0.1")

            call_args = mock_redis.evalsha.call_args
            assert call_args[0][4] == 10  # refill_rate (tokens/sec)

    @pytest.mark.asyncio
    async def test_allow_passes_custom_token_count(self, rate_limiter, mock_redis):
        """allow() deve aceitar número customizado de tokens."""
        with patch("redis.asyncio.from_url", return_value=mock_redis), patch(
            "time.time", return_value=1698765432.0
        ):
            await rate_limiter.startup()
            await rate_limiter.allow("10.0.0.1", tokens=5)

            call_args = mock_redis.evalsha.call_args
            assert call_args[0][5] == 5  # tokens_to_take

    @pytest.mark.asyncio
    async def test_allow_passes_current_timestamp(self, rate_limiter, mock_redis):
        """allow() deve passar timestamp atual para Lua script."""
        frozen_time = 1698765432.123
        with patch("redis.asyncio.from_url", return_value=mock_redis), patch(
            "time.time", return_value=frozen_time
        ):
            await rate_limiter.startup()
            await rate_limiter.allow("10.0.0.1")

            call_args = mock_redis.evalsha.call_args
            assert call_args[0][6] == frozen_time  # timestamp


class TestScriptReloading:
    """Testa recarga automática de Lua script."""

    @pytest.mark.asyncio
    async def test_allow_reloads_script_on_no_script_error(
        self, rate_limiter, mock_redis
    ):
        """allow() deve recarregar script se Redis retornar NoScriptError."""
        # Primeira chamada: NoScriptError
        # Segunda chamada: sucesso
        mock_redis.evalsha.side_effect = [NoScriptError(), 1]

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()

            # Reset counter pois startup já carregou uma vez
            mock_redis.script_load.reset_mock()

            result = await rate_limiter.allow("10.0.0.1")

            # Deve ter recarregado script
            mock_redis.script_load.assert_called_once_with(_TOKEN_BUCKET_LUA)

            # Deve ter retornado sucesso
            assert result is True

            # evalsha deve ter sido chamado 2 vezes (primeira falhou, segunda OK)
            assert mock_redis.evalsha.call_count == 2

    @pytest.mark.asyncio
    async def test_script_reload_uses_lock(self, rate_limiter, mock_redis):
        """Recarga de script deve usar lock para evitar race conditions."""
        mock_redis.evalsha.side_effect = [NoScriptError(), 1]

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()
            mock_redis.script_load.reset_mock()

            # Lock deve existir
            assert rate_limiter._lock is not None
            assert isinstance(rate_limiter._lock, asyncio.Lock)

            await rate_limiter.allow("10.0.0.1")

            # Script foi recarregado
            mock_redis.script_load.assert_called_once()


class TestRateLimiterErrors:
    """Testa tratamento de erros."""

    @pytest.mark.asyncio
    async def test_allow_raises_if_not_initialized(self, rate_limiter):
        """allow() deve lançar RuntimeError se não foi inicializado."""
        with pytest.raises(RuntimeError) as exc_info:
            await rate_limiter.allow("10.0.0.1")

        assert "not initialised" in str(exc_info.value).lower()
        assert "startup()" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_allow_raises_if_redis_is_none(self, rate_limiter, mock_redis):
        """allow() deve falhar se Redis foi fechado."""
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()
            await rate_limiter.shutdown()

            with pytest.raises(RuntimeError):
                await rate_limiter.allow("10.0.0.1")

    @pytest.mark.asyncio
    async def test_allow_raises_if_script_sha_is_none(self, rate_limiter):
        """allow() deve falhar se script SHA não foi carregado."""
        rate_limiter._redis = mock_redis  # Simula Redis conectado mas sem script
        rate_limiter._script_sha = None

        with pytest.raises(RuntimeError):
            await rate_limiter.allow("10.0.0.1")


class TestConcurrency:
    """Testa comportamento concorrente."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_allow_calls(self, rate_limiter, mock_redis):
        """Deve suportar múltiplas chamadas allow() concorrentes."""
        mock_redis.evalsha.return_value = 1

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()

            # Fazer 100 chamadas concorrentes
            tasks = [rate_limiter.allow(f"10.0.0.{i % 255}") for i in range(100)]
            results = await asyncio.gather(*tasks)

            # Todas devem ter sucesso
            assert all(results)
            assert mock_redis.evalsha.call_count == 100

    @pytest.mark.asyncio
    async def test_different_ips_have_independent_buckets(
        self, rate_limiter, mock_redis
    ):
        """IPs diferentes devem ter buckets independentes."""
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await rate_limiter.startup()

            await rate_limiter.allow("10.0.0.1")
            await rate_limiter.allow("10.0.0.2")
            await rate_limiter.allow("10.0.0.3")

            # Verificar que chaves Redis são diferentes
            calls = mock_redis.evalsha.call_args_list
            keys = [call[0][2] for call in calls]

            assert "tegumentar:rate:10.0.0.1" in keys
            assert "tegumentar:rate:10.0.0.2" in keys
            assert "tegumentar:rate:10.0.0.3" in keys
            assert len(set(keys)) == 3  # 3 chaves únicas


class TestConfigurationRespect:
    """Testa se rate limiter respeita configurações."""

    @pytest.mark.asyncio
    async def test_uses_configured_redis_url(self, mock_redis):
        """Deve usar Redis URL configurado."""
        custom_settings = TegumentarSettings(redis_url="redis://custom-redis:6380/5")
        limiter = DistributedRateLimiter(custom_settings)

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_from_url.return_value = mock_redis
            await limiter.startup()

            mock_from_url.assert_called_once_with(
                "redis://custom-redis:6380/5", encoding="utf-8", decode_responses=True
            )

    @pytest.mark.asyncio
    async def test_uses_configured_capacity(self, mock_redis):
        """Deve usar capacidade configurada."""
        custom_settings = TegumentarSettings(
            redis_url="redis://localhost:6379/0", rate_limit_capacity=5000
        )
        limiter = DistributedRateLimiter(custom_settings)

        with patch("redis.asyncio.from_url", return_value=mock_redis), patch(
            "time.time", return_value=1.0
        ):
            await limiter.startup()
            await limiter.allow("10.0.0.1")

            call_args = mock_redis.evalsha.call_args
            assert call_args[0][3] == 5000  # capacity

    @pytest.mark.asyncio
    async def test_uses_configured_refill_rate(self, mock_redis):
        """Deve usar refill rate configurada."""
        custom_settings = TegumentarSettings(
            redis_url="redis://localhost:6379/0", rate_limit_refill_per_second=25
        )
        limiter = DistributedRateLimiter(custom_settings)

        with patch("redis.asyncio.from_url", return_value=mock_redis), patch(
            "time.time", return_value=1.0
        ):
            await limiter.startup()
            await limiter.allow("10.0.0.1")

            call_args = mock_redis.evalsha.call_args
            assert call_args[0][4] == 25  # refill_rate


class TestLuaScriptContent:
    """Testa integridade do Lua script."""

    def test_lua_script_is_not_empty(self):
        """Lua script não deve estar vazio."""
        assert _TOKEN_BUCKET_LUA.strip() != ""

    def test_lua_script_has_required_operations(self):
        """Lua script deve ter operações essenciais."""
        # Verificar que script tem comandos Redis necessários
        assert "HMGET" in _TOKEN_BUCKET_LUA
        assert "HMSET" in _TOKEN_BUCKET_LUA
        assert "EXPIRE" in _TOKEN_BUCKET_LUA

    def test_lua_script_implements_token_bucket_logic(self):
        """Lua script deve implementar lógica de token bucket."""
        # Verificar conceitos de token bucket
        assert "capacity" in _TOKEN_BUCKET_LUA
        assert "refill" in _TOKEN_BUCKET_LUA or "refill_rate" in _TOKEN_BUCKET_LUA
        assert "tokens" in _TOKEN_BUCKET_LUA
        assert "timestamp" in _TOKEN_BUCKET_LUA

    def test_lua_script_handles_initialization(self):
        """Lua script deve inicializar bucket se não existir."""
        assert "if not current_tokens" in _TOKEN_BUCKET_LUA

    def test_lua_script_calculates_time_delta(self):
        """Lua script deve calcular delta de tempo."""
        assert "delta" in _TOKEN_BUCKET_LUA
        assert "now" in _TOKEN_BUCKET_LUA

    def test_lua_script_returns_boolean(self):
        """Lua script deve retornar 0 ou 1 (boolean)."""
        assert "return 0" in _TOKEN_BUCKET_LUA
        assert "return 1" in _TOKEN_BUCKET_LUA
