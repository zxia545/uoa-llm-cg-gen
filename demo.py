import time
import os
import re
import subprocess
from typing import Optional

from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def extract_python_code(text: str) -> Optional[str]:
    """
    Extract the Python code block enclosed by triple backticks, accounting for different capitalizations
    and extra newlines or spaces.
    
    Args:
        text (str): The text containing the code block.
        
    Returns:
        Optional[str]: Extracted Python code block, or None if no code block is found.
    """
    # Regex to find the python code block, case-insensitive match for 'python'
    pattern = r"import numpy as np\s*(.*?)\s*```"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    
    if match:
        # Extract code block
        return "import numpy as np\n" + match.group(1).strip()
    
    return None

def get_prompt(question):
    system_prompt = "You are an AI tutor specializing in computer graphics. Given the following question, generate a Python script using Plotly that visualizes the scenario described and save it as html. The code should be self-contained and executable, including all necessary imports and definitions."
    template = """
##Question:
{question}

##Output:

Fill below Python code in a standalone code block.
```python
import numpy as np
import plotly.graph_objects as go
import time

fig.write_html(f'temp_{{time.time()}}.html')
```

"""
    message = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": template.format(question=question)}
    ]
    return message


def get_code(prompt, max_retry=3):
    completion = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=prompt,
    )
    
    return_message = completion.choices[0].message.content
    python_code = extract_python_code(return_message)
    if python_code is None and max_retry > 0:
        get_code(prompt, max_retry - 1)
    return python_code


def process_question(question):
    prompt = get_prompt(question)
    python_code = get_code(prompt)
    
    if python_code is None:
        print(f'For question {question}- cannot find valid test code, passed by it.')
        return
    
    
    temp_folder = "./temp"
    
    test_path = os.path.join(temp_folder, "test.py")

    with open(test_path, 'w') as f:
        f.write(python_code)
        
    try:
        # Use os.path.abspath to get the full path of test.py
        full_test_path = os.path.abspath(os.path.join(temp_folder, 'test.py'))

        # Run the test with timeout and capture output
        output = subprocess.check_output(
            [
                "bash", "-c",
                # Using conda run with absolute path to the script
                f"conda run -n lm-eval python {full_test_path}"
            ],
            cwd=temp_folder,  # Ensure correct working directory
            timeout=10,  # Timeout in seconds
            stderr=subprocess.STDOUT
        ).decode('utf-8')

    except subprocess.TimeoutExpired:
        print(f'Timeout occurred for question {question}')
    except Exception as e:
        print(f'Exception for question {question} {str(e)}')



if __name__ == "__main__":
    questions = [
        """Given is a light source at the position
L=(1,3,0)T
and an object with the point
P=(1,2,1)
.

If we draw the projected shadow of the object on the plane y=1, what is the position P' of the point P projected on the plane y=1?

Hint: Make yourself an illustration of the situation.
""",
"""Given is a plane 3x+2y-z=3 and a ray

$p(t)=\left(\begin{array}{l}1 \\ 0 \\ 1\end{array}\right)+t *\left(\begin{array}{c}-1 \\ c \\ 0\end{array}\right)$

For what value of c is the ray parallel to the plane?
"""
    ]
    for question in questions:
        process_question(question)
