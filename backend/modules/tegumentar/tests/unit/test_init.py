"""
Testes unitários para backend.modules.tegumentar.__init__

Testa lazy imports via __getattr__:
- TegumentarSettings via lazy import
- TegumentarModule via lazy import
- get_settings via lazy import
- AttributeError para nomes inválidos

Padrão Pagani: Lazy loading 100%, __all__ validado.

EM NOME DE JESUS - LAZY IMPORTS PERFEITOS!
"""

import pytest


class TestLazyImports:
    """Testa lazy imports via __getattr__."""

    def test_imports_tegumentar_settings_lazily(self):
        """Deve importar TegumentarSettings via __getattr__ (linhas 18-21)."""
        from backend.modules.tegumentar import TegumentarSettings

        # Deve ser a classe real
        assert TegumentarSettings.__name__ == "TegumentarSettings"
        # Deve ter o campo postgres_dsn
        assert "postgres_dsn" in TegumentarSettings.model_fields

    def test_imports_tegumentar_module_lazily(self):
        """Deve importar TegumentarModule via __getattr__ (linhas 22-25)."""
        from backend.modules.tegumentar import TegumentarModule

        # Deve ser a classe real
        assert TegumentarModule.__name__ == "TegumentarModule"
        # Deve ter métodos startup/shutdown
        assert hasattr(TegumentarModule, "startup")
        assert hasattr(TegumentarModule, "shutdown")

    def test_imports_get_settings_lazily(self):
        """Deve importar get_settings via __getattr__ (linhas 26-29)."""
        from backend.modules.tegumentar import get_settings

        # Deve ser a função real
        assert callable(get_settings)
        # Deve retornar TegumentarSettings
        settings = get_settings()
        assert settings.__class__.__name__ == "TegumentarSettings"

    def test_raises_attribute_error_for_invalid_name(self):
        """Deve levantar AttributeError para nome inválido (linha 30)."""
        import backend.modules.tegumentar as tegumentar

        with pytest.raises(AttributeError) as exc_info:
            _ = tegumentar.InvalidAttribute

        assert "has no attribute 'InvalidAttribute'" in str(exc_info.value)

    def test_all_exports_are_valid(self):
        """__all__ deve conter apenas exports válidos."""
        import backend.modules.tegumentar as tegumentar

        # __all__ deve ter 3 itens
        assert len(tegumentar.__all__) == 3
        assert "TegumentarSettings" in tegumentar.__all__
        assert "TegumentarModule" in tegumentar.__all__
        assert "get_settings" in tegumentar.__all__

        # Todos devem ser importáveis
        for name in tegumentar.__all__:
            assert hasattr(tegumentar, name)


class TestModuleMetadata:
    """Testa metadata do módulo."""

    def test_has_docstring(self):
        """Módulo deve ter docstring descritivo."""
        import backend.modules.tegumentar as tegumentar

        assert tegumentar.__doc__ is not None
        assert "Tegumentar" in tegumentar.__doc__
        assert "Epiderme" in tegumentar.__doc__
        assert "Derme" in tegumentar.__doc__
        assert "Hipoderme" in tegumentar.__doc__
