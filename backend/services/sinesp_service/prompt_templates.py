"""Maximus Sinesp Service - Prompt Templates.

This module defines prompt templates used for interacting with Large Language
Models (LLMs) within the Maximus AI's Sinesp Service. These templates are
designed to structure queries to the LLM, guiding it to perform specific tasks
such as analyzing Sinesp vehicle information, extracting insights, or generating
recommendations.

By using predefined prompt templates, Maximus AI can ensure consistent and
effective communication with the LLM, optimizing its ability to interpret public
security data and provide intelligent support for investigations.
"""

# Prompt template for LLM to analyze Sinesp vehicle information
SINESP_ANALYSIS_PROMPT = """
Analyze the following Sinesp vehicle information and provide a concise summary, 
identify any potential risks or anomalies, and suggest actionable recommendations.

Vehicle Information (JSON):
{vehicle_info}

Consider the following:
- Is the vehicle reported stolen?
- What is the age of the vehicle? (older vehicles might be used for illicit activities)
- Are there any unusual combinations of model, color, or location?

Provide your analysis in the following structure:
Summary:
[Concise summary of the vehicle information]

Potential Risks:
[List any potential risks or anomalies identified, e.g., stolen vehicle, suspicious age]

Recommendations:
[List actionable recommendations, e.g., alert authorities, investigate owner, cross-reference with other databases]
"""

# You can define more prompt templates here for other LLM tasks
# For example:
# SINESP_REPORT_GENERATION_PROMPT = """
# Generate a formal report based on the Sinesp vehicle analysis.
# ...
# """
