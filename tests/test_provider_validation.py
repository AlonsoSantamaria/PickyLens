import asyncio
import json
import pytest
from openai.types.responses import Response
from app.config import load_settings
from app.core.contracts import PREProposal
from app.providers.openai_adapter import OpenAIProvider
from app.providers.telemetry import calls


def response(text, status='completed'):
    return Response.model_validate(dict(id='resp-test', created_at=0, model='test-model', object='response',
        status=status, parallel_tool_calls=False, tool_choice='auto', tools=[],
        output=[dict(id='msg-test',type='message',role='assistant',status='completed',
            content=[dict(type='output_text',text=text,annotations=[])])],
        usage=dict(input_tokens=10,output_tokens=20,total_tokens=30,
            input_tokens_details=dict(cached_tokens=0,cache_write_tokens=0),output_tokens_details=dict(reasoning_tokens=2))))


@pytest.mark.parametrize('case',['valid','invalid','truncated','refusal'])
def test_structured_response_retains_usage_and_never_retries(tmp_path,caplog,case):
    async def run():
        provider=OpenAIProvider(load_settings(tmp_path,{'OPENAI_API_KEY':'test-only'}))
        valid=dict(readiness='green',findings=[],clarifications=[],requirements=['Compare options'],improved_prompt='Compare options')
        text=json.dumps(valid) if case=='valid' else '{"private-input":"DO-NOT-LOG"}'
        r=response(text,'incomplete' if case=='truncated' else 'completed')
        if case=='refusal': r.output=[]
        sent=[]
        async def fake(**kwargs): sent.append(kwargs); return r
        provider.client.responses.create=fake
        bucket=[]; token=calls.set(bucket)
        try:
            if case=='valid':
                result=await provider.generate_structured({'request':'Compare options'},PREProposal,'pre')
                assert result.requirements[0].text=='Compare options'
            else:
                with pytest.raises(ValueError):
                    await provider.generate_structured({'request':'Compare options'},PREProposal,'pre')
            assert len(sent)==1 and sent[0]['text']['format']['strict'] is True
            assert sent[0]['store'] is False
            assert len(bucket)==1 and bucket[0].total_tokens==30
            assert bucket[0].response_id=='resp-test'
            if case=='invalid':
                assert bucket[0].error_type=='ValidationError'
                assert 'structured_schema_invalid' in caplog.text
            if case=='truncated': assert bucket[0].error_type=='IncompleteResponse'
            if case=='refusal': assert bucket[0].error_type=='MissingStructuredResult'
            assert 'DO-NOT-LOG' not in caplog.text and 'private-input' not in caplog.text
        finally:
            calls.reset(token)
            await provider.client.close()
    asyncio.run(run())
