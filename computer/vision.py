# this file convert computer screenshots into format that can be
# sent to the vision - capable LLM for screen understanding.

import base64
from io import BytesIO

from computer.llm import create_vision_llm

def image_to_base64(image):
    """Convert a PIL image into a base64 encoded PNG string.""" # PIL = Python Imaging Library,It allows Python to work with images.
    # Base64 is a way of converting binary data into text

    buffer = BytesIO()
    image.save(buffer,format="PNG")

    image_byte = buffer.getvalue()

    return base64.b64encode(image_byte).decode("utf-8")

def analyze_screen(image):
    """Send a screenshot to the vision LLM and return its description."""

    image_base64 = image_to_base64(image)

    llm = create_vision_llm()

    response = llm.invoke(
        [
            {
                "role":"user",
                "content":[
                    {
                        "type":"text",
                        "text":(
                            "Analyze this computer screenshot. "
                            "Describe the visible application, important UI elements"
                            "and the current state of screen."
                        ),

                    },
                    {
                        "type":"image_url",
                        "image_url":{
                            "url":f"data:image/png;base64,{image_base64}",
                        }
                    }
                ]
            }
        ]
    )
    return response.content