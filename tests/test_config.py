from app.config import load_settings


def test_dotenv_and_process_precedence(tmp_path):
    (tmp_path / ".env").write_text("OPENAI_API_KEY=local-test-only\nPICKYLENS_MODEL=file-model\n")
    local = load_settings(tmp_path, {})
    assert local.api_key.get_secret_value() == "local-test-only"
    assert "local-test-only" not in repr(local)
    override = load_settings(tmp_path, {"OPENAI_API_KEY":"process-test-only", "PICKYLENS_MODEL":"process-model"})
    assert override.model == "process-model"
    assert override.api_key.get_secret_value() == "process-test-only"


def test_production_ignores_repository_dotenv(tmp_path):
    (tmp_path / ".env").write_text("OPENAI_API_KEY=local-test-only\n")
    settings = load_settings(tmp_path, {"PICKYLENS_ENV":"production"})
    assert not settings.api_key.get_secret_value()
