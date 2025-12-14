import os
from openai import OpenAI

def test_grammar_analysis():
    """Test grammar analysis using OpenAI-compatible API."""
    client = OpenAI(
        base_url=os.getenv("ENGLISH_RPG_BASE_URL", "http://localhost:3000/v1"),
        api_key=os.getenv("ENGLISH_RPG_API_KEY", "dummy-key")
    )

    messages = [
        {
            "role": "system",
            "content": """You are an English grammar expert specializing in clear, systematic explanations for French speakers.

Your role is to analyze and explain English grammar patterns, structures, and rules in a way that makes them easy to understand and remember.

ANALYSIS APPROACH:
- Break down complex structures into simple components
- Show clear patterns and rules
- Provide multiple varied examples
- Explain exceptions and special cases clearly
- Make connections to French grammar when helpful (similarities and differences)
- Use visual organization (tables, lists, hierarchies)

EXPLANATION STYLE:
- Start with the core rule or pattern
- Show the structure clearly
- Provide abundant examples with translations
- Highlight what French speakers typically struggle with
- Give memory aids and recognition tips
- Include common error patterns to avoid

VISUAL CLARITY:
- Use Markdown tables for paradigies and comparisons
- Use bullet points for rules and examples
- Use bold for emphasis on key points
- Structure information hierarchically

Make grammar logical, systematic, and demystified. Help students see the patterns rather than memorizing isolated rules."""
        },
        {
            "role": "user",
            "content": "Explain the difference between 'make' and 'do' in English."
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "response_schema",
                    "schema": {
                        "type": "object",
                        "required": [
                            "grammar_analysis"
                        ],
                        "properties": {
                            "examples": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": [
                                        "english",
                                        "french"
                                    ],
                                    "properties": {
                                        "note": {
                                            "type": "string",
                                            "description": "Optional explanation"
                                        },
                                        "french": {
                                            "type": "string"
                                        },
                                        "english": {
                                            "type": "string"
                                        }
                                    }
                                },
                                "description": "Key example sentences"
                            },
                            "key_points": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Summary of main takeaways"
                            },
                            "grammar_analysis": {
                                "type": "string",
                                "description": "Complete grammar analysis in Markdown format"
                            }
                        },
                        "additionalProperties": False
                    }
                }
            }
        )
        print("Response:")
        print(response.choices[0].message.content)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_grammar_analysis()
