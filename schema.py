from pydantic import BaseModel, Field, field_validator
from typing import List
import re

class Assertion(BaseModel):
    verificationId: str = Field(..., description="Snake case identifier like 'homepage_loads' or 'fuel_discount_displayed'")
    description: str = Field(..., description="MUST start with 'Verify that' followed by what to check")
    
    @field_validator('verificationId')
    @classmethod
    def validate_verification_id(cls, v):
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            # Auto-fix: convert to snake_case
            v = re.sub(r'[.-]', '_', v.lower())
            v = re.sub(r'^\d+_\d+_?', '', v)  # Remove leading numbers like "1.1_"
            v = re.sub(r'^_+', '', v)  # Remove leading underscores
            if not v:
                v = "test_assertion"
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v.startswith("Verify that"):
            # Auto-fix: prepend "Verify that"
            v = f"Verify that {v[0].lower()}{v[1:]}" if v else "Verify that the assertion passes"
        return v

class Phase(BaseModel):
    phaseNumber: int
    objective: str = Field(..., description="The action to perform like 'Navigate to homepage' or 'Click the Get Started button'")
    assertions: List[Assertion]
    
    @field_validator('objective')
    @classmethod
    def validate_objective(cls, v):
        # List of action verbs that should start an objective
        action_verbs = ['Navigate', 'Click', 'Fill', 'Scroll', 'Select', 'Enter', 'Submit', 
                       'Open', 'Close', 'Hover', 'Type', 'Press', 'Wait', 'Refresh', 'Load', 'Tap']
        
        # Check if objective starts with an action verb
        if not any(v.startswith(verb) for verb in action_verbs):
            # If it starts with "Verify" or "Check", convert it
            if v.startswith('Check'):
                # Extract what's being checked and convert to navigation
                if 'section' in v.lower():
                    v = f"Scroll to the {v.replace('Check ', '').replace('Check the ', '')}"
                else:
                    v = f"Navigate to view {v.replace('Check ', '').replace('Check the ', '')}"
            elif v.startswith('Verify'):
                v = f"Navigate to the section containing {v.replace('Verify ', '').replace('Verify the ', '')}"
            elif not any(v.startswith(verb) for verb in action_verbs):
                # Default to navigation if no action verb
                v = f"Navigate to {v}"
        
        return v

class QAPlan(BaseModel):
    title: str
    phases: List[Phase]

class QATestFile(BaseModel):
    name: str = Field(..., description="Descriptive test name for the YAML file")
    qa_plan: QAPlan
