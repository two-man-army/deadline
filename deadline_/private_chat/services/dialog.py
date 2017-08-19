"""
Functions related to Dialog objects
"""
from accounts.models import User
from private_chat.models import Dialog


def get_or_create_dialog_token(owner: User, opponent: User) -> str:
    """
    Gets or Creates a Dialog between the two users.
    Returns owner's dialog token. If the token is expired, it resets them
    """
    dialog: Dialog = Dialog.objects.get_or_create_dialog_with_users(owner, opponent)
    if dialog.tokens_are_expired():
        dialog.refresh_tokens(True)

    if dialog.owner == owner:
        dialog_token = dialog.owner_token
    else:
        dialog_token = dialog.opponent_token

    return dialog_token
