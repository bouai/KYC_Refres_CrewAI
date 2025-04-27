from crewai import Tasks
from tools import vision_tool 
from agents import researcher_agent, kyc_analyst_agent, Screening_agent

#Research task
research_task = Tasks(
    name="Research Task",
    description=(
        "Read the user image from {path}",
        "Extract text from the image using VisionTool from the retrieved image",
        "Provide the extracted text to the KYC Analyst Agent for further processing.",
    ),
    expected_output="Extracted text from the image",
    tools=[vision_tool],
    agent=researcher_agent,
)
