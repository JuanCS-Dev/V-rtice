from pathlib import Path

class ValidationError(Exception):
    pass

def sanitize_file_path(path: str) -> Path:
    """
    Sanitizes a file path to prevent path traversal.
    - Resolves the absolute path.
    - Ensures the path is within the user's home directory (as a safe base).
    - Ensures the file exists.
    """
    try:
        # Resolve o caminho absoluto para evitar ataques de `..`
        absolute_path = Path(path).resolve()
        home_dir = Path.home().resolve()

        # Verifica se o caminho resolvido está dentro de um diretório seguro (ex: home)
        # Em um ambiente de produção, isso seria um diretório mais restrito
        if not absolute_path.is_relative_to(home_dir):
            raise ValidationError(f"Path is outside of the allowed directory.")

        # Verifica se o arquivo realmente existe
        if not absolute_path.is_file():
            raise ValidationError(f"File does not exist at the specified path.")

        return absolute_path

    except FileNotFoundError:
        raise ValidationError("File not found.")
    except Exception as e:
        # Captura outras exceções de path (ex: nome de arquivo muito longo)
        raise ValidationError(f"Invalid path provided: {e}")