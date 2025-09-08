
from .login import create_user, delete_user
def add_user(username, password, role='user'):
    return create_user(username, password, role)
def remove_user(requestor_username, username):
    return delete_user(requestor_username, username)
