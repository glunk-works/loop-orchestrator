from cryptfile_backend import EncryptedFileKeyring


def _backend(tmp_path, monkeypatch, passphrase: str = "correct horse battery staple"):
    data_path = tmp_path / "keyring_data.enc"
    passphrase_path = tmp_path / "passphrase"
    passphrase_path.write_text(passphrase)

    monkeypatch.setenv("LOOP_ENGINE_KEYRING_FILE", str(data_path))
    monkeypatch.setenv("LOOP_ENGINE_KEYRING_PASSPHRASE_FILE", str(passphrase_path))
    return EncryptedFileKeyring()


def test_get_password_returns_none_when_no_file_exists(tmp_path, monkeypatch) -> None:
    backend = _backend(tmp_path, monkeypatch)

    assert backend.get_password("loop-engine", "anthropic_api_key") is None


def test_set_then_get_password_round_trips(tmp_path, monkeypatch) -> None:
    backend = _backend(tmp_path, monkeypatch)

    backend.set_password("loop-engine", "anthropic_api_key", "sk-ant-fake-value")

    assert backend.get_password("loop-engine", "anthropic_api_key") == "sk-ant-fake-value"


def test_separate_service_username_pairs_do_not_collide(tmp_path, monkeypatch) -> None:
    backend = _backend(tmp_path, monkeypatch)

    backend.set_password("loop-engine", "anthropic_api_key", "key-one")
    backend.set_password("other-service", "other-user", "key-two")

    assert backend.get_password("loop-engine", "anthropic_api_key") == "key-one"
    assert backend.get_password("other-service", "other-user") == "key-two"


def test_delete_password_removes_entry(tmp_path, monkeypatch) -> None:
    backend = _backend(tmp_path, monkeypatch)
    backend.set_password("loop-engine", "anthropic_api_key", "sk-ant-fake-value")

    backend.delete_password("loop-engine", "anthropic_api_key")

    assert backend.get_password("loop-engine", "anthropic_api_key") is None


def test_wrong_passphrase_returns_none_instead_of_raising(tmp_path, monkeypatch) -> None:
    writer = _backend(tmp_path, monkeypatch, passphrase="correct passphrase")
    writer.set_password("loop-engine", "anthropic_api_key", "sk-ant-fake-value")

    (tmp_path / "passphrase").write_text("wrong passphrase")
    reader = EncryptedFileKeyring()

    assert reader.get_password("loop-engine", "anthropic_api_key") is None
