def is_admin(user_id: int, admin_ids: list[int]) -> bool:
    return user_id in admin_ids
