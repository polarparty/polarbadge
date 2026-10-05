import os
import re

import click

from polarbadge.service.geekevents import get_client
from polarbadge.service.config import get_config
from polarbadge.service.render import render_card, render_to_image
from .spec import design

_client = get_client()
_config = get_config()

REGEX_UUID = re.compile(r"^[0-9a-f\-]{30,50}$")

def pp34_everyone():
    generate_badges()

@click.option("--user", "-u", multiple=True)
def pp34_users(user: list[int]):
    users = list(map(int, user))
    generate_badges(user_ids=users)

def generate_badges(user_ids: list | None = None):
    click.echo("Generating badges...")
    crew_members = _client.get_crew_members().members
    if user_ids is not None:
        crew_members = [crew_member for crew_member in crew_members if crew_member.user_id in user_ids]

    number_of_crew_members = len(crew_members)
    click.echo(f"Generating badge for {number_of_crew_members} crew members, output path "
               f"{_config.general.output_path}")
    for i, crew in enumerate(crew_members):
        profile_pic = _client.get_picture(crew.profile_image)
        filename = f"{crew.user_id}-{crew.full_name.replace(' ', '')}"
        file_path = os.path.join(_config.general.output_path, filename)

        crew_name = " ".join(crew.crew.replace("_", " ").split())

        data = {
            "name": crew.full_name,
            "nick": crew.username,
            "crew": crew_name,
            "profile_picture_content": profile_pic,
            "user_id": crew.user_id,
        }

        if REGEX_UUID.match(crew.username):
            click.secho("\tUser has UUID for nick, using first name as nick", fg="yellow")
            data["name"] = ""
            data["nick"] = crew.first_name

        html = render_card(design=design, **data)
        with open(file_path + ".html", "w") as f:
            f.write(html)

        render_to_image(file_path + ".bmp", design, html)

        click.secho(f"{i+1}/{number_of_crew_members} - Generating badge for {crew.full_name}", fg="blue")


@click.option("--users-file", help="File we'll put the registered data into", default="./users.csv")
def register(users_file: str):
    crew_list = _client.get_crew_members()
    crew_map = {crew_member.user_id: crew_member for crew_member in crew_list.members}

    _continue = True
    while _continue:
        member_id = click.prompt("GE User ID (write 'exit' if you're done)", type=str)
        if member_id == "exit":
            _continue = False
            return

        try:
            user = crew_map.get(int(member_id))
        except ValueError:
            click.secho(f"Invalid user ID", fg="red")
            continue

        if user is None:
            click.secho(f"User {member_id } not found, try again", fg="red")
            continue

        click.secho(f"Found user {user.username} ({user.full_name})", fg="blue")
        try:
            nfc_id = click.prompt("NFC ID (scan card)", type=str)
        except ValueError:
            click.secho("Invalid NFC ID", fg="red")
            continue

        with open(users_file, mode="a") as f:
            line = [member_id, nfc_id, user.username, user.full_name, user.crew]
            line_formatted = ",".join(map(str, line))
            f.write(line_formatted + "\n")
            click.secho(f"Saved user: {line_formatted}", fg="green")
