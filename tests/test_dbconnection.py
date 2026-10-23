from unittest.mock import Mock

from utils import dbconnection


def test_close_db_connection_disposes_engine(monkeypatch):
    mock_engine = Mock()
    monkeypatch.setattr(dbconnection, "engine", mock_engine)

    dbconnection.close_db_connection()

    mock_engine.dispose.assert_called_once()
