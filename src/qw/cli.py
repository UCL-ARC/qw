from typing import Annotated

import typer
from loguru import logger

# Main entry point into the application
app = typer.Typer()


@app.command()
def parrot(
    example: Annotated[str, typer.Argument(help="String to print to user")],
) -> None:
    parrot_name = typer.prompt("What's your parrot's name?", default="Polly")
    shout = typer.confirm("Do you want your parrot to shout?")
    output_message = example
    if shout:
        output_message = f"{output_message.upper()}!!"
    logger.info(
        "{parrot_name}🦜: {output_message}",
        parrot_name=parrot_name,
        output_message=output_message,
    )


@app.command()
def echo(
    example: Annotated[str, typer.Argument(help="String to print to user")],
) -> None:
    logger.info("Echo: {example}", example=example)


if __name__ == "__main__":
    app()
