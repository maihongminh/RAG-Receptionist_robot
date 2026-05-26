import json
from http.client import RemoteDisconnected
from unittest.mock import patch

from app.config import Settings
from app.llm.llm_client import LLMClient


class FakeResponse:
    def __init__(self, body: dict) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.body).encode("utf-8")


def build_client(**overrides) -> LLMClient:
    client = LLMClient()
    values = {
        "database_url": "postgresql:///robo_reception",
        "default_domain": "clinic",
        "llm_provider": "none",
        "llm_model": "test-model",
        "llm_base_url": "https://api.openai.test/v1",
        "llm_timeout_seconds": 5,
        "openai_api_key": "",
        "anthropic_api_key": "",
    }
    values.update(overrides)
    client.settings = Settings(**values)
    return client


def test_llm_client_returns_none_when_disabled():
    client = build_client(llm_provider="none")

    assert client.parse_intent("xin chào", "clinic") is None


def test_llm_client_returns_none_without_api_key():
    client = build_client(llm_provider="openai", openai_api_key="")

    assert client.parse_intent("xin chào", "clinic") is None


def test_llm_client_parses_openai_compatible_response():
    body = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "domain": "clinic",
                            "intent": "appointment_booking",
                            "entities": {"booking_query": "đặt lịch"},
                            "confidence": 0.91,
                            "requires_auth": False,
                            "data_source": "none",
                            "reasoning": "User wants to book an appointment.",
                        }
                    )
                }
            }
        ]
    }
    client = build_client(llm_provider="openai", openai_api_key="test-key")

    with patch("urllib.request.urlopen", return_value=FakeResponse(body)) as mocked_urlopen:
        intent = client.parse_intent("đặt lịch", "clinic")

    assert intent is not None
    assert intent.intent == "appointment_booking"
    assert intent.entities["booking_query"] == "đặt lịch"
    assert intent.data_source == "none"

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["messages"][1]["content"] == "đặt lịch"


def test_llm_client_parses_ollama_response():
    body = {
        "message": {
            "content": json.dumps(
                {
                    "domain": "clinic",
                    "intent": "knowledge_search",
                    "entities": {"knowledge_query": "tôi cần tìm hiểu thông tin"},
                    "confidence": 0.82,
                    "requires_auth": False,
                    "data_source": "rag",
                    "reasoning": "User asks for general guidance.",
                }
            )
        }
    }
    client = build_client(
        llm_provider="ollama",
        llm_model="qwen2.5:3b",
        llm_base_url="http://localhost:11434",
    )

    with patch("urllib.request.urlopen", return_value=FakeResponse(body)) as mocked_urlopen:
        intent = client.parse_intent("tôi cần tìm hiểu thông tin", "clinic")

    assert intent is not None
    assert intent.intent == "knowledge_search"
    assert intent.entities["knowledge_query"] == "tôi cần tìm hiểu thông tin"
    assert intent.data_source == "rag"

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "http://localhost:11434/api/chat"
    assert payload["format"] == "json"
    assert payload["stream"] is False


def test_llm_client_normalizes_ollama_payload_with_intent_in_data_source():
    body = {
        "message": {
            "content": json.dumps(
                {
                    "domain": "clinic",
                    "data_source": "knowledge_search",
                    "knowledge_query": "quy trình trả kết quả",
                    "confidence": 0.72,
                    "requires_auth": False,
                    "reasoning": "User asks for a workflow.",
                }
            )
        }
    }
    client = build_client(
        llm_provider="ollama",
        llm_model="qwen2.5:3b",
        llm_base_url="http://localhost:11434",
    )

    with patch("urllib.request.urlopen", return_value=FakeResponse(body)):
        intent = client.parse_intent("Quy trình trả kết quả như thế nào?", "clinic")

    assert intent is not None
    assert intent.intent == "knowledge_search"
    assert intent.data_source == "rag"
    assert intent.entities["knowledge_query"] == "quy trình trả kết quả"


def test_llm_client_infers_ollama_intent_from_top_level_entity_key():
    body = {
        "message": {
            "content": json.dumps(
                {
                    "domain": "clinic",
                    "data_source": "rag",
                    "knowledge_query": "quy trình check-in bệnh nhân",
                    "confidence": 0.64,
                    "requires_auth": False,
                    "reasoning": "User asks for guidance.",
                }
            )
        }
    }
    client = build_client(
        llm_provider="ollama",
        llm_model="qwen2.5:3b",
        llm_base_url="http://localhost:11434",
    )

    with patch("urllib.request.urlopen", return_value=FakeResponse(body)):
        intent = client.parse_intent("Quy trình check-in bệnh nhân như thế nào?", "clinic")

    assert intent is not None
    assert intent.intent == "knowledge_search"
    assert intent.data_source == "rag"
    assert intent.entities["knowledge_query"] == "quy trình check-in bệnh nhân"


def test_llm_client_normalizes_nested_intent_payload():
    body = {
        "message": {
            "content": json.dumps(
                {
                    "medical_advice": {
                        "entities": {},
                        "confidence": 0.7,
                        "requires_auth": False,
                        "data_source": "none",
                        "reasoning": "User asks what service to choose.",
                    }
                }
            )
        }
    }
    client = build_client(
        llm_provider="ollama",
        llm_model="qwen2.5:3b",
        llm_base_url="http://localhost:11434",
    )

    with patch("urllib.request.urlopen", return_value=FakeResponse(body)):
        intent = client.parse_intent("nên sử dụng loại nào?", "clinic")

    assert intent is not None
    assert intent.intent == "medical_advice"
    assert intent.data_source == "none"


def test_llm_client_returns_none_on_invalid_response():
    client = build_client(llm_provider="openai", openai_api_key="test-key")
    body = {"choices": [{"message": {"content": "not-json"}}]}

    with patch("urllib.request.urlopen", return_value=FakeResponse(body)):
        assert client.parse_intent("đặt lịch", "clinic") is None


def test_llm_client_returns_none_on_timeout():
    client = build_client(
        llm_provider="ollama",
        llm_model="qwen2.5:3b",
        llm_base_url="http://localhost:11434",
    )

    with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        assert (
            client.generate_formatted_answer(
                question="Tôi có lịch hẹn nào không?",
                intent_name="personal_data",
                context="patient_name: Nguyễn Văn A",
                is_private=True,
            )
            is None
        )


def test_llm_client_returns_none_on_remote_disconnect():
    client = build_client(
        llm_provider="ollama",
        llm_model="qwen2.5:3b",
        llm_base_url="http://localhost:11434",
    )

    with patch("urllib.request.urlopen", side_effect=RemoteDisconnected("closed")):
        assert client.parse_intent("xin chào", "clinic") is None


def test_llm_client_formats_answers_with_ollama_only():
    body = {"message": {"content": "Bạn có 1 lịch hẹn vào 08:00 với bệnh nhân Nguyễn Văn A."}}
    client = build_client(
        llm_provider="ollama",
        llm_model="qwen2.5:3b",
        llm_base_url="http://localhost:11434",
    )

    with patch("urllib.request.urlopen", return_value=FakeResponse(body)) as mocked_urlopen:
        answer = client.generate_formatted_answer(
            question="Tôi có lịch hẹn nào không?",
            intent_name="personal_data",
            context="patient_name: Nguyễn Văn A\nstart_time: 08:00:00",
            is_private=True,
        )

    assert answer == "Bạn có 1 lịch hẹn vào 08:00 với bệnh nhân Nguyễn Văn A."
    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "http://localhost:11434/api/chat"
    assert payload["stream"] is False
    assert "CONTEXT" in payload["messages"][1]["content"]
    assert "AUDIENCE_ROLE: guest" in payload["messages"][1]["content"]


def test_llm_client_does_not_format_answers_with_openai():
    client = build_client(llm_provider="openai", openai_api_key="test-key")

    assert (
        client.generate_formatted_answer(
            question="Tôi có lịch hẹn nào không?",
            intent_name="personal_data",
            context="patient_name: Nguyễn Văn A",
            is_private=True,
        )
        is None
    )
