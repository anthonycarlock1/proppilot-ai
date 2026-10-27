from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

Hazard = Literal['fire_or_smoke', 'gas_odor', 'active_flooding', 'sparking_or_live_wiring', 'structural_collapse', 'carbon_monoxide_alarm']
Priority = Literal['low', 'medium', 'high', 'emergency']
Status = Literal['open', 'in_progress', 'resolved']


class Assessment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: Literal['hvac', 'plumbing', 'electrical', 'general']
    category_model_version: str = Field(min_length=1, max_length=64)
    category_provider: Literal['local', 'sagemaker']
    urgency: Priority
    urgency_model_version: str = Field(min_length=1, max_length=64)
    urgency_provider: Literal['local', 'sagemaker']
    recommended_priority: Priority
    confirmed_hazards: list[Hazard] = Field(max_length=6)
    escalation_reasons: list[str] = Field(max_length=6)
    policy_version: str = Field(min_length=1, max_length=64)
    manual_review_required: Literal[True]

    @model_validator(mode='after')
    def policy_consistent(self):
        if self.recommended_priority != ('emergency' if self.confirmed_hazards else self.urgency):
            raise ValueError('Inconsistent recommended priority')
        if bool(self.escalation_reasons) != bool(self.confirmed_hazards):
            raise ValueError('Inconsistent hazard reasons')
        return self


class DraftRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    description: str = Field(min_length=3, max_length=4000, strict=True)
    assessment: Assessment


class CreateTicket(BaseModel):
    model_config = ConfigDict(extra='forbid')
    assessment_id: UUID
    property_label: str = Field(min_length=2, max_length=120, strict=True)
    unit: str = Field(default='', max_length=40, strict=True)
    confirm_reviewed: Literal[True]

    @field_validator('confirm_reviewed', mode='before')
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError('Explicit review confirmation is required')
        return value

    @field_validator('property_label', 'unit')
    @classmethod
    def trim(cls, value, info):
        value = value.strip()
        if info.field_name == 'property_label' and len(value) < 2:
            raise ValueError('Property name is required')
        return value


class StatusUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Status
    expected_version: StrictInt = Field(ge=1)
