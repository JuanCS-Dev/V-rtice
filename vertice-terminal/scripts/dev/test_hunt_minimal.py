"""Minimal test of first hunt command"""
import typer
from typing_extensions import Annotated
from typing import Optional

app = typer.Typer(name="hunt", help="Test")

@app.command()
async def search(
    query: str = typer.Argument(..., help="IOC query to hunt for"),
    ioc_type: Optional[str] = typer.Option(None, help="IOC type"),
    json_output: bool = typer.Option(False, help="Output as JSON"),
    verbose: bool = typer.Option(False, help="Verbose output"),
):
    """Test command"""
    pass

if __name__ == "__main__":
    from typer.main import get_command
    try:
        cmd = get_command(app)
        print("✅ Minimal hunt test works!")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
