import click

if __name__=="__main__":
    click.echo("Running as main...")

    list0 = [item for item in range(10)]
    list1 = [item for item in list0 if item % 2 == 2]

    for i in list0:
        click.echo(f"Hello {i}")
    click.echo(f"Done with {len(list0)} iterations.")

    for i in list1:
        click.echo(f"Hello {i}")
    click.echo(f"Done with {len(list1)} iterations.")