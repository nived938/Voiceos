import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session", autouse=True)
def qapp_session():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    try:
        app.closeAllWindows()
        app.sendPostedEvents()
        app.processEvents()
    except Exception:
        pass
