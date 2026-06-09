import json
import streamlit as st
from openai import OpenAI


def generate_ticket_from_subject(ticket_type, subject, examples):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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

Existing examples:
{json.dumps(examples, indent=2)}

Return ONLY valid JSON in this exact format:
{json.dumps(output_format, indent=2)}

Writing rules:
- Entity types = (invoices, vacancy, placements, clients, candidates, timesheets, subject, interviews, applications, projects)

When generating prerequisites and steps, do not only consider examples with similar subjects.
Also look for prerequisite activities contained within other examples.
For example:
    - If creating an Invoice requires a Candidate, Client, Placement or Contract to exist, reuse the prerequisite steps that explain how to create those records.
    - If creating a Placement requires a Candidate and Client, reuse those prerequisite creation steps.
    - If creating a Timesheet requires a Placement, reuse the Placement creation steps.
You may combine information from multiple examples to build complete prerequisites or steps.

- Number each prerequisite and step.
- Each line should be concise and punctual.
- Avoid colloquial terms like succesfully or correctly or does not work.
- Do not invent unrelated features.
- Do not invent steps, if they are unknown, stop where you are and type 'NEXT LINES UNKNOWN'
- Do not include markdown.

- Entity types = (invoices, vacancy, placements, clients, candidates, timesheets, subject, interviews, applications, projects)
- All steps that need users to navigate to a main list ' Navigate to the (Entity Types) main list'
- In steps if an entity type is opened ammend 'The '(Entity Types) Details' form will be displayed.'

Match the style of the ticket type.

- For Bugs, include:
  - a short clear summary
  - prerequisites
  - steps to replicate
  - a clear outcome
  - a clear expected outcome

- If generating a Bug, use Bug examples for the overall bug report structure.
- If Test Case examples are provided, use them to understand detailed prerequisites and steps.
- Each Entity type on a bug reports
- For Bug prerequisites, use the main numbered prerequisite headings only where appropriate.
- Bug reports should be shorter than Test Cases but still detailed enough to reproduce the issue.

- For Test Cases, include:
  - prerequisites
  - steps to replicate
  - pass criteria


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