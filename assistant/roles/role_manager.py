from config import get_role

class RoleManager:
    DEFAULT_ROLES = {
    }

    def __init__(self, default_role=None, user_id=None, source=None):
        self.user_id = user_id
        self.source = source
        if default_role is not None:
            self.role_prompt = default_role
        else:
            # Сначала пробуем получить роль из config.yaml
            config_role = get_role(source)
            if config_role and config_role.strip():
                self.role_prompt = config_role
                print(f"[ROLE] Используется роль из config.yaml для источника '{source}'")
            elif source in self.DEFAULT_ROLES:
                self.role_prompt = self.DEFAULT_ROLES[source]
                print(f"[ROLE] Используется роль по умолчанию для источника '{source}'")
            else:
                self.role_prompt = self.DEFAULT_ROLES["local"]
                print(f"[ROLE] Используется роль 'local' по умолчанию (источник '{source}' не найден)")
        self.custom_roles = {}  # user_id: role_text

    def set_role(self, role_description, user_id=None):
        if user_id:
            self.custom_roles[user_id] = role_description
        else:
            self.role_prompt = role_description

    def get_role(self, user_id=None):
        if user_id and user_id in self.custom_roles:
            return self.custom_roles[user_id]
        return self.role_prompt
