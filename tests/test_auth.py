from auth import create_user, verify_user
from db import list_users

def test_user_creation_and_login():
    # Create a user
    create_user("alice", "password123", "user")

    # Verify it exists in DB
    users = list_users()
    assert len(users) == 1
    assert users[0]["username"] == "alice"

    # Login success
    user = verify_user("alice", "password123")
    assert user is not None
    assert user["username"] == "alice"
    assert user["role"] == "user"

    # Login failure
    failed = verify_user("alice", "wrongpass")
    assert failed is None

def test_duplicate_user_not_created():
    create_user("bob", "123", "user")
    create_user("bob", "456", "admin")   # duplicate username

    users = list_users()
    assert len(users) == 1  # still only one Bob