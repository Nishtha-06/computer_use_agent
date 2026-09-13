# this file tests whether the vision capable LLM can analyze a computer
# screenshot and select an appropriate computer control tool.

import base64
from io import BytesIO

from computer.llm import create_vision_llm
from computer.observer import capture_screen
from computer.tools import(
    tool_screenshot,
    tool_open_application,
    tool_open_url,
    tool_move_mouse,
    tool_click,
    tool_press_key,
    tool_type_text,
)

# capture the current computer screen.
image = capture_screen()

# Convert the screenshot into PNG bytes.
buffer = BytesIO()
image.save(buffer,format="PNG")

image_bytes = buffer.getvalue()

# convert the PNG bytes into Base64
image_base64 = base64.b64encode(image_bytes).decode("utf-8")

# List the computer tools available to the vision model.
tools = [
    tool_screenshot,
    tool_open_application,
    tool_open_url,
    tool_move_mouse,
    tool_click,
    tool_press_key,
    tool_type_text,
]

# create the vision-capable LLM
llm = create_vision_llm()

# give tool to vision model
llm_with_tools = llm.bind_tools(tools)

# Ask the model to look at the current screen and decide what action
# should be taken to complete the user's goal.
response = llm_with_tools.invoke(
    [
        {
            "role":"user",
            "content":[
                {
                    "type":"text",
                    "text":(
                        "Look at the current computer screenshot."
                        "The user's goal is: Opne Notepad and type "
                        "'Hello Computer Use Agent'."
                        "Based on the current screen, choose the "
                        "next computer tool that should be executed."
                    ),
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":f"data:image/png;base64,{image_base64}",
                    },
                },
            ],
        }
    ]
)

print("Vision + Tool Selection: ")
if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"Tool: {tool_call['name']}")
        print(f"Arguments: {tool_call['args']}")
else:
    print("No tool was selected.")
    print("Model response:")
    print(response.content)
