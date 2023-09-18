from typing import Annotated

import typer as typer
from loguru import logger

# Main entry point into the application
app = typer.Typer()


@app.command()
def parrot(
        example: Annotated[str, typer.Argument(help="String to print to user")]
) -> None:
    logger.info("🦜 {example}", example=example)


@app.command()
def echo(
        example: Annotated[str, typer.Argument(help="String to print to user")]
) -> None:
    logger.info("Echo: {example}", example=example)


if __name__ == "__main__":
    app()
