# this file tests where the Groq vision model can receive a screenshot
# and desribe what is visible on the computer screen.

import base64

from computer.llm import create_vision_llm
from computer.observer import capture_screen

image = capture_screen()

#convert screenshot to PNG bytes
image_bytes = None

from io import BytesIO

buffer = BytesIO()
image.save(buffer,format = "PNG")
image_bytes = buffer.getvalue()

# convert the image to base64
image_base64 = base64.b64encode(image_bytes).decode("utf-8")

# create the vision model
llm = create_vision_llm()

# send text + screenshot to the vision model.
response = llm.invoke(
    [
        {
            "role":"user",
            "content":[
                {
                    "type":"text",
                    "text":(
                        "Look at this computer screentshot."
                        "Describe what applicatiob is currently visible "
                        "and what the user can see."
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

print("Vision model response:")
print(response.content)