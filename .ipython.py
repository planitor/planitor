# Planitor configuration file for ipython.

from platform import python_version, python_implementation

c.TerminalInteractiveShell.confirm_exit = False
c.InteractiveShellApp.exec_PYTHONSTARTUP = False

c.InteractiveShell.banner1 = "Python %s (%s)" % (
    python_version(),
    python_implementation(),
)
c.InteractiveShell.banner2 = "Welcome to the Planitor IPython shell!\n"

c.InteractiveShellApp.extensions = ["autoreload"]

c.InteractiveShellApp.exec_lines = [
    "from planitor.models import *",
    "from planitor.database import get_db",
    "session_ctx = get_db()",
    "db = next(session_ctx)",
]
