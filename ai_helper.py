import json
import streamlit as st
from openai import OpenAI

from entities import (
    extract_entities,
    expand_entities_with_dependencies,
    aliases_for_entities,
)

from db import get_entity_examples


def generate_ticket_from_subject(ticket_type, subject, examples):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    base_entities = extract_entities(subject)
    expanded_entities = expand_entities_with_dependencies(base_entities)
    entity_terms = aliases_for_entities(expanded_entities)

    entity_examples = get_entity_examples(entity_terms)

    if ticket_type == "Test Case":
        output_format = {
            "prerequisites": "",
            "steps_to_replicate": "",
            "expected_outcome": "",
        }
    else:
        output_format = {
            "summary": "",
            "prerequisites": "",
            "steps_to_replicate": "",
            "outcome": "",
            "expected_outcome": "",
        }

    prompt = f"""
You are an experienced QA tester writing tickets for Eclipse Software LTD.

You must generate a detailed {ticket_type} using the same format, level of detail,
and wording style as the existing examples.

Subject:
{subject}


Return ONLY valid JSON in this exact format:
{json.dumps(output_format, indent=2)}

Detected Dependency entities:
{json.dumps(expanded_entities, indent=2)}

Subject-related examples:
{json.dumps(examples, indent=2)}

Entity-related examples:
{json.dumps(entity_examples, indent=2)}


Writing rules:
- Before writing prerequisites, identify the main action being tested.
- Subject-related examples should be used to determine the overall ticket purpose.
- Entity-related examples should be used to build prerequisites and steps.
- You may combine information from multiple examples, if it is needed.
- Entity types = (invoices, vacancy, placements, clients, candidates, timesheets, subject, interviews, applications, projects)
- Number each prerequisite and step.
- Each line should be concise and punctual.
- Avoid colloquial terms like succesfully or correctly or does not work.
- Do not invent unrelated features.
- Do not invent steps, if they are unknown, stop where you are and type 'NEXT LINES UNKNOWN'
- Do not include markdown.


    Match the style of the ticket type.

    - For Bugs, include:
        - a short clear summary
        - prerequisites
        - steps to replicate
        - a clear outcome
        - a clear expected outcome

    - If generating a Bug, use Bug examples for the overall bug report structure.
    - If Test Case examples are provided, use them to understand detailed prerequisites and steps.
    - For Bug prerequisites, use the main numbered prerequisite headings only where appropriate.
    - Bug reports should be shorter than Test Cases but still detailed enough to reproduce the issue.

    - For Test Cases, include:
        - prerequisites
        - steps to replicate
        - pass criteria


    Important prerequisite rule:
        - Prerequisites must only include records or setup that must already exist before the test starts.
        - Before writing prerequisites, identify the main action being tested.
        - Do NOT put the main action from the subject into prerequisites.
        - Dependency entities may be used in prerequisites only if they must already exist before the main action.
        - Do NOT list the target entity from the subject as a prerequisite.
        - If the subject says the user is creating an entity, that entity must be created in the steps, not listed as an existing prerequisite.
        - Entity examples can be reused for setup instructions, but only when that entity is not the main entity being created.

        Example:
        Subject: The system errors when the user creates an interview record from the interview main list.

        Correct prerequisites:
        1. User must have access to a candidate record.

        Incorrect prerequisites:
        1. User must have access to an interview record.
        2. User must have access to an interview record setup.

        Correct steps:
        1. Navigate to the interviews main list.
        2. Click the 'Add a new record' button. The 'Create New Interview' form will be displayed.
        3. Populate all mandatory fields, including linking the candidate mentioned in prerequisite 1.
        4. Click 'Finish'.
        5. Observe the error.

    Important steps to replicate rule:
        - All steps that need users to navigate to a main list ' Navigate to the (Entity Types) main list' 
        - In steps if an entity type is opened ammend 'The '(Entity Types) Details' form will be displayed.'




- Do not include markdown.
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt,
    )

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError:
        st.error("AI response could not be parsed. Please try again.")
        return {}