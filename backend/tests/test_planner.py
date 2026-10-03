import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.schemas import ResearchRequest, ResearchPlan
from app.agents.planner import ResearchPlanner, PlannerError
from app.services.llm import LLMService, LLMNotConfiguredError

@pytest.fixture
def mock_laptop_plan():
    return ResearchPlan(
        decision_category="electronics/product research",
        user_goal="Find a laptop for AI/ML development, programming and occasional gaming",
        budget="₹1,20,000",
        hard_constraints=["at least 16GB RAM", "budget max ₹1,20,000"],
        preferences=["good battery life", "occasional gaming capability"],
        important_attributes=["RAM capacity", "Processor (CPU)", "GPU performance", "Battery life hours", "Price"],
        research_questions=[
            "Which laptops under ₹1,20,000 provide at least 16GB RAM and RTX GPU?",
            "What is the battery life performance reported in coding & ML benchmarks?",
            "What are current prices across merchants?"
        ],
        required_search_types=["web", "shopping", "youtube"],
        comparison_criteria=["RAM size", "Price in INR", "Battery life (hours)", "GPU model"]
    )

@pytest.fixture
def mock_hotel_plan():
    return ResearchPlan(
        decision_category="travel/hotel research",
        user_goal="Find a 4-star beach resort hotel in Goa for 4 nights under $800",
        budget="$800",
        hard_constraints=["4-star rating", "beachfront/beach resort", "Goa location"],
        preferences=["free breakfast", "swimming pool"],
        important_attributes=["star rating", "location proximity to beach", "nightly rate", "guest rating"],
        research_questions=[
            "Which 4-star beach resorts in Goa cost under $800 for 4 nights?",
            "Which resorts include free breakfast and swimming pool?"
        ],
        required_search_types=["web", "youtube"],
        comparison_criteria=["Total cost for 4 nights", "Guest review score", "Distance to beach"]
    )

@pytest.fixture
def mock_generic_comparison_plan():
    return ResearchPlan(
        decision_category="electronics/product research",
        user_goal="Compare Sony WH-1000XM5 vs Bose QuietComfort Ultra noise cancelling headphones",
        budget="$400",
        hard_constraints=["Active Noise Cancellation (ANC)", "price under $400"],
        preferences=["comfort", "long battery life"],
        important_attributes=["ANC quality", "audio fidelity", "comfort", "battery life"],
        research_questions=[
            "Which headphones have superior Active Noise Cancellation?",
            "What do reviewers say about comfort for long sessions?"
        ],
        required_search_types=["web", "shopping", "youtube"],
        comparison_criteria=["ANC performance rating", "Battery hours", "Price"]
    )

@pytest.mark.asyncio
async def test_planner_laptop_research_request(mock_laptop_plan):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_structured_output = AsyncMock(return_value=mock_laptop_plan)

    planner = ResearchPlanner(llm_service=mock_llm)
    prompt = "I need a laptop for AI/ML development, programming and occasional gaming. My budget is ₹1,20,000. I want at least 16GB RAM and good battery life."
    
    plan = await planner.create_plan(prompt)

    assert plan.decision_category == "electronics/product research"
    assert "laptop" in plan.user_goal.lower()
    assert plan.budget == "₹1,20,000"
    assert "at least 16GB RAM" in plan.hard_constraints
    assert "good battery life" in plan.preferences
    assert "RAM capacity" in plan.important_attributes
    assert len(plan.research_questions) > 0
    assert "shopping" in plan.required_search_types
    assert "youtube" in plan.required_search_types
    assert len(plan.comparison_criteria) > 0

@pytest.mark.asyncio
async def test_planner_hotel_travel_request(mock_hotel_plan):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_structured_output = AsyncMock(return_value=mock_hotel_plan)

    planner = ResearchPlanner(llm_service=mock_llm)
    prompt = "Find a 4-star beach resort hotel in Goa for 4 nights under $800 with free breakfast and pool."
    
    plan = await planner.create_plan(prompt)

    assert plan.decision_category == "travel/hotel research"
    assert plan.budget == "$800"
    assert "4-star rating" in plan.hard_constraints
    assert "free breakfast" in plan.preferences
    assert "web" in plan.required_search_types

@pytest.mark.asyncio
async def test_planner_generic_product_comparison(mock_generic_comparison_plan):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_structured_output = AsyncMock(return_value=mock_generic_comparison_plan)

    planner = ResearchPlanner(llm_service=mock_llm)
    prompt = "Compare Sony WH-1000XM5 vs Bose QuietComfort Ultra noise cancelling headphones under $400."
    
    plan = await planner.create_plan(prompt)

    assert "Sony WH-1000XM5" in plan.user_goal
    assert plan.budget == "$400"
    assert len(plan.research_questions) >= 2

@pytest.mark.asyncio
async def test_budget_extraction(mock_laptop_plan):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_structured_output = AsyncMock(return_value=mock_laptop_plan)

    planner = ResearchPlanner(llm_service=mock_llm)
    plan = await planner.create_plan("Budget test query")

    assert plan.budget == "₹1,20,000"

@pytest.mark.asyncio
async def test_hard_constraint_extraction(mock_laptop_plan):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_structured_output = AsyncMock(return_value=mock_laptop_plan)

    planner = ResearchPlanner(llm_service=mock_llm)
    plan = await planner.create_plan("Constraint test query")

    assert len(plan.hard_constraints) > 0
    assert any("16GB" in c for c in plan.hard_constraints)

@pytest.mark.asyncio
async def test_preferences_extraction(mock_laptop_plan):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_structured_output = AsyncMock(return_value=mock_laptop_plan)

    planner = ResearchPlanner(llm_service=mock_llm)
    plan = await planner.create_plan("Preference test query")

    assert len(plan.preferences) > 0
    assert any("battery" in p.lower() for p in plan.preferences)

@pytest.mark.asyncio
async def test_research_questions_generation(mock_laptop_plan):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_structured_output = AsyncMock(return_value=mock_laptop_plan)

    planner = ResearchPlanner(llm_service=mock_llm)
    plan = await planner.create_plan("Questions test query")

    assert isinstance(plan.research_questions, list)
    assert len(plan.research_questions) >= 1

@pytest.mark.asyncio
async def test_search_type_generation(mock_laptop_plan):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_structured_output = AsyncMock(return_value=mock_laptop_plan)

    planner = ResearchPlanner(llm_service=mock_llm)
    plan = await planner.create_plan("Search types test query")

    assert set(plan.required_search_types).issubset({"web", "shopping", "youtube"})

@pytest.mark.asyncio
async def test_invalid_and_empty_input_handling():
    planner = ResearchPlanner()

    with pytest.raises(ValueError, match="Research request query cannot be empty."):
        await planner.create_plan("")

    with pytest.raises(ValueError, match="Research request query cannot be empty."):
        await planner.create_plan("   ")

    with pytest.raises(ValueError, match="Input request must be a string or ResearchRequest instance."):
        await planner.create_plan(12345)  # Invalid type

@pytest.mark.asyncio
async def test_unconfigured_llm_raises_error():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_structured_output = AsyncMock(side_effect=LLMNotConfiguredError("openai"))

    planner = ResearchPlanner(llm_service=mock_llm)

    with pytest.raises(LLMNotConfiguredError):
        await planner.create_plan("Valid request string")
