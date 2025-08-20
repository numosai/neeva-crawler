"""
Neeva-Crawler: Website analysis tool (Legacy CLI entry point)
This file is maintained for backward compatibility.
The refactored code is in the src/ directory.
"""
import asyncio
from src.cli.main import main


if __name__ == "__main__":
    asyncio.run(main())