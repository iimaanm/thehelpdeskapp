from .constants import (
    ADMIN_GUIDE_TOPICS,
    GUIDE_TOPIC_CREATE_NEW_TICKETS,
    ROLE_ADMIN,
    ROLE_USER,
    USER_GUIDE_TOPICS,
)


def is_admin(user):
    return getattr(user, "role", None) == ROLE_ADMIN


def can_edit_ticket(user, ticket):
    return is_admin(user) or ticket.user_id == user.id


def can_delete_ticket(user, ticket):
    return is_admin(user) or ticket.user_id == user.id


def can_access_guide(user, guide_topic):
    role = getattr(user, "role", None)
    if role == ROLE_ADMIN and guide_topic in ADMIN_GUIDE_TOPICS:
        return True
    if role == ROLE_USER and guide_topic in USER_GUIDE_TOPICS:
        return True
    return guide_topic == GUIDE_TOPIC_CREATE_NEW_TICKETS