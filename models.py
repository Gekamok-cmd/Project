class Performer:


    def __init__(self, name, role, skill_level=5):
        self.name = name
        self.role = role
        self.skill_level = skill_level
        self.is_available = True

    def perform(self):
        if not self.is_available:
            return f"{self.name} не доступен для выступления"

        if self.skill_level > 7:
            return f"{self.name} ({self.role}) показывает великолепное выступление!"
        elif self.skill_level > 5:
            return f"{self.name} ({self.role}) показывает хорошее выступление."
        else:
            return f"{self.name} ({self.role}) показывает базовое выступление."

    def train(self):
        self.skill_level = min(10, self.skill_level + 1)
        return f"{self.name} повысил навык до {self.skill_level}"

    def toggle_availability(self):
        self.is_available = not self.is_available
        return self.is_available


class Circus:

    def __init__(self, name):
        self.name = name
        self.performers = []

    def add_performer(self, performer):
        self.performers.append(performer)

    def remove_performer(self, performer_id):
        if 0 <= performer_id < len(self.performers):
            return self.performers.pop(performer_id)
        return None

    def get_best_performers(self, min_skill=8):
        return [p for p in self.performers if p.skill_level >= min_skill]

    def get_stats(self):

        total = len(self.performers)
        available = sum(1 for p in self.performers if p.is_available)
        avg_skill = sum(p.skill_level for p in self.performers) / total if total > 0 else 0

        roles = {}
        for p in self.performers:
            roles[p.role] = roles.get(p.role, 0) + 1

        return {
            'total_performers': total,
            'available_performers': available,
            'average_skill': round(avg_skill, 2),
            'roles_distribution': roles,
            'circus_name': self.name
        }

    def perform_show(self):
        if not any(p.is_available for p in self.performers):
            return "Нет доступных артистов для шоу"

        performances = []
        for performer in self.performers:
            if performer.is_available:
                performances.append(performer.perform())

        return {
            'show_name': f'Шоу {self.name}',
            'performances': performances,
            'total_performers': len(performances)
        }