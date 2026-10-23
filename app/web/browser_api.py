"""Explicit browser actions; no host lifecycle inference or automatic follow-up."""
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from app.core import pre, evaluation
from app.core import next as next_stage
from app.core.contracts import ApprovedIntent, Answer, Evaluation

class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request: str = Field(min_length=1, max_length=20000)

class AnswerRequest(ReviewRequest):
    answer: str = Field(min_length=1, max_length=30000)

# POST deliberately extracts requirements from the exact chosen host request.
# This avoids accepting a proposed PRE rewrite as user intent.
def router(provider):
    routes = APIRouter(prefix='/api/browser')

    @routes.post('/pre')
    async def request_review(body: ReviewRequest):
        return await pre.review(provider, body.request)

    @routes.post('/post')
    async def answer_review(body: AnswerRequest):
        proposal = await pre.review(provider, body.request)
        intent = ApprovedIntent(version=1, original_request=body.request,
            approved_prompt=body.request, approval_action='explicit_check_of_host_submitted_request',
            accepted_clarifications={}, requirements=proposal.requirements)
        answer = Answer(text=body.answer, metadata={'origin':'gemini_web'})
        result = await evaluation.evaluate(provider, intent, [answer], 'post')
        return {'intent':intent, 'answer':answer, 'assessment':result}

    class RepairRequest(BaseModel):
        model_config = ConfigDict(extra='forbid')
        intent: ApprovedIntent
        answer: Answer
        assessment: Evaluation

    @routes.post('/next')
    async def repair(body: RepairRequest):
        return await next_stage.generate(provider, body.intent, body.assessment, body.answer)

    return routes
