import os
import re
import tempfile
import subprocess
import base64
from typing import Optional
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def encode_image(image_path: str) -> str:
    """
    Encode the given image as a base64 string.
    
    Args:
        image_path (str): The path to the image to be encoded.
        
    Returns:
        str: The base64-encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def extract_python_code(text: str) -> Optional[str]:
    """
    Extract the Python code block enclosed by triple backticks.
    
    Args:
        text (str): The text containing the code block.
        
    Returns:
        Optional[str]: Extracted Python code block, or None if no code block is found.
    """
    pattern = r"```python(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        code = matches[0].strip()
        return code
    return None


def get_image_description_prompt(image_base64: str) -> list:
    """
    Construct the prompt message to be sent to the OpenAI API for image description.
    
    Args:
        image_base64 (str): The base64-encoded string of the image.
        
    Returns:
        list: A list of messages for the OpenAI API.
    """
    system_prompt = (
        "You are an AI assistant specializing in computer graphics. "
        "Given the following image, provide a detailed description of the main objects, shapes, and visual effects present in the image. "
        "Focus on identifying key elements like the type of objects, their positions, their interactions (e.g., cutting, overlapping), and any effects such as shading, lighting, or reflections. "
        "The description should be concise, informative, and focus on elements that are most relevant for recreating the scene programmatically."
    )
    template = "Provide a detailed and concise description of the main objects, shapes, interactions, and visual effects in the image, focusing on details relevant for generating a graphical representation."

    # Constructing the message
    message = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": template},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ]
        }
    ]
    return message


def get_prompt(question: str, image_description: str, image_base64: str) -> list:
    """
    Construct the prompt message to be sent to the OpenAI API.
    
    Args:
        question (str): The question text.
        image_description (str): The description of the image.
        image_base64 (str): The base64-encoded string of the image.
        
    Returns:
        list: A list of messages for the OpenAI API.
    """
    system_prompt = (
        "You are an AI assistant specializing in computer graphics. "
        "Given the following question, image description, and image, generate a complete, self-contained Python script using Plotly that visualizes the scenario described. "
        "The code should include all necessary imports and definitions and save the figure as an HTML file. "
        "Please output only the code inside a standalone Python code block, without additional explanations."
    )
    template = f"""
## Question:
{question}

## Image Description:
{image_description}

## Output:
Provide the Python code in a standalone code block.

```python
import numpy as np
import plotly.graph_objects as go
import time

fig.write_html(f'temp_{{time.time()}}.html')
```
"""

    # Constructing the message
    message = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": template},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ]
        }
    ]
    return message


def get_code(prompt, max_retry=3):
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=prompt,
    )
    return_message = response.choices[0].message.content
    python_code = extract_python_code(return_message)
    if python_code is None:
        if max_retry > 0:
            print(f"Code extraction failed. Retrying... ({max_retry} retries left)")
            return get_code(prompt, max_retry - 1)
        else:
            print("Max retries exceeded. Could not extract code.")
            return None
    return python_code


def process_question(question: str, image_path: str):
    # Encode the image to base64
    image_base64 = encode_image(image_path)
    
    # Get image description
    image_description_prompt = get_image_description_prompt(image_base64)
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=image_description_prompt,
    )
    image_description = response.choices[0].message.content.strip()
    
    
    print(f"Image Description: {image_description}")
    
    # Create the prompt
    prompt = get_prompt(question, image_description, image_base64)
    
    # Get the Python code from GPT
    python_code = get_code(prompt)
    
    if python_code is None:
        print(f'For question "{question}" - cannot find valid code, skipping it.')
        return
    
    # Create a temporary directory
    temp_folder = os.path.abspath("./temp")
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    test_path = os.path.join(temp_folder, "test.py")

    with open(test_path, 'w') as f:
        f.write(python_code)
        
    try:
        # Run the test with timeout and capture output
        output = subprocess.check_output(
            ["python", test_path],
            cwd=temp_folder,
            timeout=30,
            stderr=subprocess.STDOUT
        ).decode('utf-8')
        print(f"Execution output:\n{output}")
    except subprocess.TimeoutExpired:
        print(f'Timeout occurred for question "{question}"')
    except subprocess.CalledProcessError as e:
        print(f'Execution failed for question "{question}". Error:\n{e.output.decode("utf-8")}')
    except Exception as e:
        print(f'Exception for question "{question}": {str(e)}')
    finally:
        # Clean up the temp folder
        # shutil.rmtree(temp_folder)  # Uncomment this line to delete the temp folder
        pass  # Remove this line if you uncomment the above line


if __name__ == "__main__":
    # Example question
    question = """
    A plane n.p=d defines a half-space, where the half-space are all points where n.p<=d.
    For example, for the plane x=0 the half space are all points with an x-coordinate <=0.

    Using this definition we can now define a "cut-sphere" as the intersection of a sphere S and a half-space defined by the plane P. I.e., the "cut-sphere" contains all points which are inside the sphere and inside the half-space defined by P. The image below shows an example.
    """
    # Path to the image (uploaded image path)
    image_path = "./data/demo_image.png"
    
    # Process the question with the provided image
    process_question(question, image_path)
