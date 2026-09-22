# This file tests planner intent, coordinate grounding, and semantic click recovery.

from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from computer import agent as agent_module
from computer.agent import ComputerUseAgent
from computer.controller import click_point_from_bounding_box, validate_screenshot_point
from computer.planner import TaskPlanner
from computer.retry import RetryManager
from computer.task_context import TaskContext


class FakePlannerLLM:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        return SimpleNamespace(content=next(self.responses))


def test_calculator_click_intent_is_preserved():
    for target in ("5", "7", "+"):
        planner = TaskPlanner()
        planner.llm = FakePlannerLLM(
            [f"1. tool_open_application('calc')\n2. tool_click(target='{target}')"]
        )
        plan = planner.create_plan(
            f"Open Calculator and click the {target} button"
        )
        assert "tool_click" in plan
        assert "tool_press_key" not in plan


def test_click_grounding_validates_points_and_boxes():
    assert validate_screenshot_point(10, 20, (100, 100)) == (10, 20)
    assert click_point_from_bounding_box([10, 20, 30, 40], (100, 100)) == (20, 30)
    assert click_point_from_bounding_box([100, 200, 200, 300], (400, 400)) == (150, 250)

    for bounding_box in ([100, 200, 100, 300], [100, 300, 200, 300]):
        try:
            click_point_from_bounding_box(bounding_box, (400, 400))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid zero-size bounding box was accepted")

    for point in [(-1, 10), (100, 10), (10, 100)]:
        try:
            validate_screenshot_point(*point, (100, 100))
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-bounds point was accepted")


def test_semantic_click_failure_blocks_nearby_repeat():
    context = TaskContext("click the 5 button")
    context.record_semantic_failure(100, 100)
    assert context.is_near_failed_click(120, 115)
    assert not context.is_near_failed_click(130, 130)


def test_vision_history_includes_rejection_reason_and_coordinate():
    image = Image.new("RGB", (400, 300), "white")
    rejection = {
        "status": "rejected",
        "tool": "tool_click",
        "reason": "That region already failed. Choose a different coordinate.",
    }
    context = TaskContext("click the 5 button")
    context.add_action(
        "tool_click",
        {"target": None, "x": [107, 849]},
        "execution_rejected",
        rejection,
    )

    class FakeVision:
        def __init__(self):
            self.prompt = ""

        def bind(self, **kwargs):
            return self

        def invoke(self, messages):
            self.prompt = messages[0]["content"][0]["text"]
            return SimpleNamespace(content="", tool_calls=[])

    agent = ComputerUseAgent.__new__(ComputerUseAgent)
    agent.llm_with_tools = FakeVision()
    agent.image_to_base64 = lambda current_image: "encoded"

    agent.ask_vision_model(
        context.goal,
        image,
        context.action_history,
        "1. tool_click",
    )

    assert "[107, 849]" in agent.llm_with_tools.prompt
    assert "execution_rejected" in agent.llm_with_tools.prompt
    assert rejection["reason"] in agent.llm_with_tools.prompt
    assert "Never select a click coordinate listed in PROHIBITED CLICK COORDINATES." in agent.llm_with_tools.prompt
    assert "PROHIBITED CLICK COORDINATES" in agent.llm_with_tools.prompt
    assert "provide bounding_box=[x1,y1,x2,y2]" in agent.llm_with_tools.prompt
    assert "Do not guess a click point when a bounding box can be identified." in agent.llm_with_tools.prompt


def test_vision_history_blocks_semantic_and_rejected_clicks_without_duplicates():
    image = Image.new("RGB", (400, 300), "white")
    context = TaskContext("click the 5 button")
    context.add_action(
        "tool_click",
        {"x": [107, 849]},
        "executed_successfully",
        {"status": "success"},
    )
    context.action_history[-1]["verification_result"] = "VERDICT=NO"
    context.add_action(
        "tool_click",
        {"x": [107, 849]},
        "execution_rejected",
        {"status": "rejected", "reason": "That region already failed."},
    )

    class FakeVision:
        def bind(self, **kwargs):
            return self

        def invoke(self, messages):
            self.prompt = messages[0]["content"][0]["text"]
            return SimpleNamespace(content="", tool_calls=[])

    agent = ComputerUseAgent.__new__(ComputerUseAgent)
    agent.llm_with_tools = FakeVision()
    agent.image_to_base64 = lambda current_image: "encoded"
    agent.ask_vision_model(context.goal, image, context.action_history, "1. tool_click")

    assert "PROHIBITED CLICK COORDINATES: [[107, 849]]" in agent.llm_with_tools.prompt
    assert "Never select a click coordinate listed in PROHIBITED CLICK COORDINATES." in agent.llm_with_tools.prompt
    assert "If the previous click received VERDICT=NO" in agent.llm_with_tools.prompt
    assert "If a click was rejected because that region already failed" in agent.llm_with_tools.prompt


def test_agent_executes_a_click_once_after_semantic_failure():
    image = Image.new("RGB", (400, 300), "white")
    click_response = SimpleNamespace(
        content="",
        tool_calls=[{"name": "tool_click", "args": {"x": [100, 100]}}],
    )
    agent = ComputerUseAgent.__new__(ComputerUseAgent)
    agent.planner = SimpleNamespace(create_plan=lambda goal: "1. tool_click")
    agent.retry_manager = RetryManager()
    agent.ask_vision_model = lambda *args: click_response
    agent.verify_task = lambda *args: "VERDICT=NO"

    with patch.object(agent_module, "capture_screen", return_value=image), \
         patch.object(agent_module, "execute_tool", return_value={"status": "success"}) as execute, \
         patch.object(agent_module, "save_click_debug", return_value="debug.png"), \
         patch.object(agent_module, "log_action"), \
         patch.object(agent_module.time, "sleep"):
        result = agent.run("Open Calculator and click the 5 button", max_steps=2)

    assert result["status"] == "max_steps_reached"
    assert execute.call_count == 1
    assert result["results"][0]["result"]["status"] == "success"
    assert result["results"][1]["result"]["status"] == "rejected"
