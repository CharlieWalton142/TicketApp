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


Generation Process:

1. Read the subject.
2. Identify the primary entity being acted upon.
3. Identify the action being performed on that entity.
4. Identify any prerequisite entities required before that action can occur.
5. Build prerequisites from those prerequisite entities only.
6. Build steps that perform the primary action.
7. Build the pass criteria outcome and expected outcome from the subject.

Entity Rules:

* Entity types are:
  invoices, vacancy, placements, clients, candidates, timesheets, interviews, applications, projects.

* The primary entity is the entity directly affected by the subject.

* A prerequisite entity is an entity that must already exist before the primary action can be performed.

* The primary entity must never appear as an existing prerequisite if the subject is creating that entity.

* Dependency entities may be used as prerequisites only when they must exist before the primary action begins.

Examples:

Subject:
"System errors when creating an interview record"

Primary entity: Interview

Action: Create

Valid prerequisites:

* Candidate
* Client
* Vacancy

Invalid prerequisites:

* Interview record already exists

Subject:
"System errors when creating an invoice"

Primary entity: Invoice

Action: Create

Valid prerequisites:

* Client
* Candidate
* Placement

Invalid prerequisites:

* Invoice already exists

Prerequisite Rules:

* Prerequisites describe system state before testing begins.
* Prerequisites must not contain actions being tested.
* Prerequisites should be concise.
* Reuse prerequisite knowledge from examples where appropriate.
* If the Primary Entity is needed in the prerequisite it should be the last prerequisite.
* If information is unavailable, do not invent it.
* there needs to be a line sperating 



Step Rules:

* Steps must reproduce the issue or execute the test.

* The primary action must appear in the steps.

* Use entity examples to determine navigation paths.

* Number all steps sequentially.

* If a main list is opened use:
  "Navigate to the [Entity] main list."

* If an entity record is opened use:
  "The '[Entity] Details' form will be displayed."

* If the next action cannot be determined from the examples, stop and write:
  "NEXT LINES UNKNOWN"

Bug Ticket Rules:

Include:

* Summary
* Prerequisites
* Steps to replicate
* Outcome
* Expected Outcome

Bug reports should:

* Be shorter than Test Cases.
* Focus on reproducing the issue.
* Use Bug examples for structure.
* Use Test Case examples for prerequisite and navigation detail.

Test Case Rules:

Include:
* Prerequisites
* Test Steps
* Pass Criteria

Test Cases should:

* Be more detailed than Bug reports.
* Include all known setup requirements.
* Include sufficient detail for another tester to execute the test without additional guidance.

Prerequisite rules:
* Use "\n\n" between numbered prerequisite groups.
* Use "\n" between the lettered steps within a prerequisite group.

Pass Criteria Rules:

- Pass Criteria must describe what is being verified and must allways start with 'Verify'.
- Pass Criteria must be written as a validation statement.
- Pass Criteria must NOT describe the result of a failed test.
- Pass Criteria must NOT repeat the Expected Outcome style used by Bug reports.
- Pass Criteria should normally correspond to the final verification step in the Test Steps section.
- If the final test step begins with "Verify", the Pass Criteria should usually contain the same verification statement.

Example:

Test Steps:
1. Create a placement.
2. Publish the placement.
3. Verify that the placement record has been published to WI.

Correct Pass Criteria:
Verify Placement records can be published to WI.

Incorrect Pass Criteria:
Users are able to publish a placement to WI.
The placement was published to WI.
The placement should be published to WI.

Output Rules:

* Number all prerequisites and steps.
* Do not use markdown.
* Do not invent features.
* Do not invent navigation paths.
* Use concise, professional language.
* Avoid terms such as "works correctly", "works successfully", or "does not work".
* Match the style of the provided examples.

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