#Entity types to help AI Generater
ENTITY_ALIASES = {
    "invoices": ["invoice", "invoices"],
    "vacancy": ["vacancy", "vacancies"],
    "placements": ["placement", "placements"],
    "clients": ["client", "clients"],
    "candidates": ["candidate", "candidates"],
    "timesheets": ["timesheet", "timesheets"],
    "subject": ["subject", "subjects"],
    "interviews": ["interview", "interviews"],
    "applications": ["application", "applications"],
    "projects": ["project", "projects"],
}

DEPENDENCIES = {
    "invoices": ["candidates", "clients", "placements"],
    "placements": ["candidates", "clients"],
    "timesheets": ["placements"],
    "vacancies": ["client"],
    "interviews": ["candidates"],
    "applications": ["candidates"],
    "projects": ["clients", "placements"],
}

def extract_entities(text: str) -> list[str]:
    found = []
    text_lower = text.lower()

    for entity, aliases in ENTITY_ALIASES.items():
        if any(alias in text_lower for alias in aliases):
            found.append(entity)

    return found


def expand_entities_with_dependencies(entities: list[str]) -> list[str]:
    expanded = set(entities)

    for entity in entities:
        for dependency in DEPENDENCIES.get(entity, []):
            expanded.add(dependency)

    return list(expanded)


def aliases_for_entities(entities: list[str]) -> list[str]:
    aliases = []

    for entity in entities:
        aliases.extend(ENTITY_ALIASES.get(entity, [entity]))

    return list(set(aliases))
