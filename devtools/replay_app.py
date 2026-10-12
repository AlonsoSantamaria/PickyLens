"""Internal Replay diagnostics. Never expose as the public application."""
from app.main import create_app
app = create_app(internal_tools=True)
