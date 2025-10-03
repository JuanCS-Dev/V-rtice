
import pytest
from unittest.mock import patch, mock_open, MagicMock
import json
from datetime import datetime, timedelta
import importlib

# Import the module we want to test
from vertice.utils import auth

# Fixture to reload the module before each test to reset the global auth_manager
@pytest.fixture(autouse=True)
def reload_auth_module():
    importlib.reload(auth)

VALID_USER_DATA = {"email": "test@example.com", "name": "Test User"}
VALID_TOKEN_DATA = {"expires_at": (datetime.now() + timedelta(hours=1)).isoformat()}
EXPIRED_TOKEN_DATA = {"expires_at": (datetime.now() - timedelta(hours=1)).isoformat()}

@patch('vertice.utils.auth.keyring')
@patch('pathlib.Path.exists')
@patch('vertice.utils.secure_storage.SecureStorage')
def test_is_authenticated_true(mock_secure_storage_class, mock_exists, mock_keyring):
    """Test that is_authenticated returns True when token is valid."""
    mock_exists.return_value = True
    mock_secure_storage_instance = mock_secure_storage_class.return_value
    mock_secure_storage_instance.load_and_decrypt.return_value = VALID_TOKEN_DATA
    
    importlib.reload(auth)
    assert auth.auth_manager.is_authenticated() is True

@patch('pathlib.Path.exists')
def test_is_authenticated_false_no_file(mock_exists):
    """Test that is_authenticated returns False when token file does not exist."""
    mock_exists.return_value = False
    assert auth.auth_manager.is_authenticated() is False

@patch('pathlib.Path.exists')
@patch('builtins.open')
def test_is_authenticated_false_expired(mock_open, mock_exists):
    """Test that is_authenticated returns False when token is expired."""
    mock_exists.return_value = True
    mock_open.return_value = mock_open(read_data=json.dumps(EXPIRED_TOKEN_DATA)).return_value
    
    assert auth.auth_manager.is_authenticated() is False

@patch('os.chmod')
@patch('vertice.utils.auth.keyring')
@patch('builtins.open', new_callable=mock_open)
def test_save_auth_data(mock_open, mock_keyring, mock_chmod):
    """Test that save_auth_data saves token and user data correctly."""
    auth.auth_manager.save_auth_data(VALID_USER_DATA, "test_token")

    # Check that keyring was called
    mock_keyring.set_password.assert_called_once_with("vertice-cli", "access_token", "test_token")

    # Check that token.json and user.json were written to
    # Check that token.enc and user.enc were written to
    assert mock_open.call_count == 2
    assert 'token.enc' in str(mock_open.call_args_list[0].args[0])
    assert 'user.enc' in str(mock_open.call_args_list[1].args[0])
@patch('vertice.utils.auth.keyring')
@patch('pathlib.Path.unlink')
@patch('pathlib.Path.exists', return_value=True)
def test_logout(mock_exists, mock_unlink, mock_keyring):
    """Test that logout deletes credentials."""
    auth.auth_manager.logout()

    mock_keyring.delete_password.assert_called_once_with("vertice-cli", "access_token")
    # Check that unlink was called for both files
    assert mock_unlink.call_count == 2

@patch('vertice.utils.auth.AuthManager.is_authenticated', return_value=False)
def test_require_auth_raises_exit(mock_is_authenticated):
    """Test that require_auth raises typer.Exit when not authenticated."""
    with pytest.raises(auth.typer.Exit):
        auth.require_auth()

@patch('vertice.utils.auth.AuthManager.is_authenticated', return_value=True)
def test_require_auth_passes(mock_is_authenticated):
    """Test that require_auth does nothing when authenticated."""
    try:
        auth.require_auth()
    except auth.typer.Exit:
        pytest.fail("require_auth() raised typer.Exit unexpectedly!")

@patch('vertice.utils.auth.AuthManager.is_authenticated', return_value=True)
@patch('vertice.utils.auth.AuthManager.has_permission', return_value=False)
def test_require_permission_raises_exit(mock_has_permission, mock_is_authenticated):
    """Test that require_permission raises typer.Exit when permission is denied."""
    # Mock get_current_user to avoid file I/O
    with patch('vertice.utils.auth.AuthManager.get_current_user', return_value=VALID_USER_DATA):
        with pytest.raises(auth.typer.Exit):
            auth.require_permission("some.permission")

@patch('vertice.utils.auth.AuthManager.is_authenticated', return_value=True)
@patch('vertice.utils.auth.AuthManager.has_permission', return_value=True)
def test_require_permission_passes(mock_has_permission, mock_is_authenticated):
    """Test that require_permission passes when user has permission."""
    try:
        auth.require_permission("some.permission")
    except auth.typer.Exit:
        pytest.fail("require_permission() raised typer.Exit unexpectedly!")


@patch('vertice.utils.auth.AuthManager.get_current_user')
def test_get_user_role(mock_get_current_user):
    """Test the logic for getting a user's role."""
    # Test super admin
    mock_get_current_user.return_value = {"email": "juan.brainfarma@gmail.com"}
    assert auth.auth_manager.get_user_role() == "super_admin"

    # Test normal user
    mock_get_current_user.return_value = {"email": "test@example.com", "role": "analyst"}
    assert auth.auth_manager.get_user_role() == "analyst"

    # Test no user
    mock_get_current_user.return_value = None
    assert auth.auth_manager.get_user_role() == "viewer"
