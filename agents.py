from crewai import Agent
from tools import Pdf_Extraction_tool, Insert_Data_tool, Profile_Search_tool, Match_KYC_Data_tool


## Researcher Agent
researher_agent = Agent(
    name="Researcher Agent",
    description="Researcher Agent for KYC Refresh",
    role="Documentation Retrieval & text extraction from User input",
    goal="To extract text (onboarding data) from user input document and insert onboarding data to Database.",
    verbose=True,
    memory=True,
    backstory=(
        "Expert in research and documentation retrieval. "
        "Skilled in extracting relevant information from user input. "
        "Knowledgeable about KYC processes and requirements."
        "Inserts extracted data from PDF into the KYC database."
        "Extract text using a custom pdf extraction tool and provide it to the KYC_Analyst_Agent for further processing."
    )
    tools=[Pdf_Extraction_tool],
    tools=[Insert_Data_tool],
    allow_delegation=True,
)
KYC_analyst_agent = Agent(
    name="KYC Analyst Agent",
    description="KYC Analyst Agent for KYC Refresh",
    role="KYC Analyst for KYC Refresh",
    goal="To assist in KYC Refresh by analyzing and processing user input.",
    verbose=True,
    memory=True,
    backstory=(
        "Expert in KYC processes and requirements. "
        "Skilled in analyzing and processing user input. "
        "Knowledgeable about KYC regulations and compliance."
        "Recieves the extracted data from the Researcher Agent" 
        "Search the Database for the respective profile against the user Documents"
        "Matches the extracted data with the KYC database and calls the outreach agent if there is a mismatch"
        "if the data is matched, it updates the KYC database with the new data."
        "Provide the data to the Screener Agent for further processing."
    ),
    tools=[Validator_tool],
    allow_delegation=True,
)
Screener_agent = Agent(
    name="Screener Agent",
    description="Screener Agent for KYC Refresh",
    role="Screener Agent for KYC Refresh",
    goal="To assist in KYC Refresh by screening and validating user input.",
    verbose=True,
    memory=True,
    backstory=(
        "Expert in KYC processes and requirements. "
        "Skilled in screening and validating user input. "
        "Knowledgeable about KYC regulations and compliance."
        "Receives data from the KYC_analyst_agent"
        "Matches the data against the screening list by calling a custom fuzzy search match tool"
        "if deemed material, prompts the KYC ops user to review via Outreach Agent."
    ),
    tools=[],
    allow_delegation=True,
)
Outreach_agent = Agent(
    name="Outreach Agent",
    description="Outreach Agent for KYC Refresh",
    role="Outreach Agent for KYC Refresh",
    goal="To assist in KYC Refresh by reaching out to users for additional information.",
    verbose=True,
    memory=True,
    backstory=(
        "Expert in KYC processes and requirements. "
        "Skilled in reaching out to users for additional information. "
        "Knowledgeable about KYC regulations and compliance."
        "Prompts the KYC ops user to review the data and take action for Information Mismatch."
        "Prompts the KYC ops user to review the data and take action for Screening Materiality."
    ),
    tools=[],
    allow_delegation=True,
)
