# parser.py

from openai import OpenAI

client = OpenAI()


def extract_skills(job_text):

    prompt = f"""
Extract technical skills from this job text.

Return JSON list.

Text:
{job_text}
"""

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[
            {"role": "user", "content": prompt}
        ],

        temperature=0
    )

    return response.choices[0].message.content