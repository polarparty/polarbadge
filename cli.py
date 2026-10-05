#!/usr/bin/env python
import click
from polarbadge.parties.pp34 import cli as pp34_cli


@click.group()
def cli():
    pass


cli.command(pp34_cli.pp34_everyone)
cli.command(pp34_cli.pp34_users)
cli.command(pp34_cli.register)


if __name__ == "__main__":
    cli()
