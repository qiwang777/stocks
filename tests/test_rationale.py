import httpx

from stock_predictor.services.rationale import RationaleService


def test_explicit_empty_key_disables_rationale_even_with_environment_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "unused-test-key")
    service = RationaleService(api_key="")
    assert service.explain("AAPL", "1d", 0.7, "UP", []) == "Rationale unavailable."
    assert service._client is None


def test_rationale_parses_success_and_handles_http_failure():
    for status, body, expected in [
        (200, {"choices": [{"message": {"content": " Test explanation. "}}]}, "Test explanation."),
        (503, {}, "Rationale unavailable."),
    ]:
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status, json=body))) as client:
            service = RationaleService(client=client, api_key="test-key")
            assert service.explain("AAPL", "1d", 0.7, "UP", []) == expected
