from typing import List, Any, Iterator, Union, Sequence, Literal

import zoneinfo
from datetime import datetime, timedelta

import click
from tabulate import tabulate

from .countryinfo import iter_countries, _get_tz_from_fzf_line


@click.group()
def main() -> None:
    pass


def _timezone_choices() -> Iterator[str]:
    yield from zoneinfo.available_timezones()
    yield from iter_countries()


def _pick_timezone() -> zoneinfo.ZoneInfo:
    from pyfzf import FzfPrompt

    fzf = FzfPrompt()
    result = fzf.prompt(
        _timezone_choices(), "--no-multi", "--header='Select a timezone'"
    )
    if result:
        return _get_tz_from_fzf_line(result[0])
    else:
        raise click.BadArgumentUsage("No timezone selected")


def _parse_timezone(s: str) -> zoneinfo.ZoneInfo:
    try:
        return zoneinfo.ZoneInfo(s)
    except zoneinfo.ZoneInfoNotFoundError:
        pass

    try:
        return zoneinfo.ZoneInfo(f"US/{s}")
    except zoneinfo.ZoneInfoNotFoundError:
        pass

    raise ValueError(f"failed to parse timezone: {s}")


def _make_unaware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None)


def _sign(f: Union[float, int]) -> str:
    return "+" if f >= 0 else "-"


def _display_timezone_diff(fi: float) -> str:
    f = int(fi) if fi.is_integer() else fi
    # display one decimal place if it only has one decimal place, else two
    if isinstance(f, int):
        s = str(f)
    else:
        s = f"{f:.1f}" if f * 10 % 1 == 0 else f"{f:.2f}"
    return f"{_sign(f)}{s}"

def _round_to(dt: datetime, strategy: Literal["up", "down", "nearest"]) -> datetime:
    if strategy == "up":
        # round up to the nearest hour
        dt += timedelta(hours=1)
        return dt.replace(minute=0, second=0, microsecond=0)
    elif strategy == "down":
        # round down to the nearest hour
        return dt.replace(minute=0, second=0, microsecond=0)
    elif strategy == "nearest":
        return _round_to(dt, "up") if dt.minute >= 30 else _round_to(dt, "down")
    else:
        raise ValueError(f"invalid rounding strategy: {strategy}")

@main.command(short_help="time in timezone")
@click.option(
    "-f",
    "--format",
    "format_",
    default="%Y-%m-%d %H:%M:%S %Z",
    help="format for printing dates",
    show_default=True,
)
@click.option(
    "-h",
    "--hours",
    "hours_",
    default=0,
    type=int,
    help="print this many localized hours in timezones",
    show_default=True,
)
@click.option(
    "--print-local/--skip-local",
    "print_local",
    default=True,
    help="print the local time as well",
)
@click.option(
    "-r",
    "--round",
    "round_",
    type=click.Choice(["up", "down", "nearest"]),
    default="down",
    help="round the time to the nearest hour",
    show_default=True,
)
@click.option(
    "--print-info/--hide-info",
    "print_tz",
    default=True,
    help="print timezone info/difference",
)
@click.argument("TZ", required=False, type=str, nargs=-1)
def tz(
    format_: str,
    hours_: int,
    print_local: bool,
    print_tz: bool,
    round_: Literal["up", "down", "nearest"],
    tz: Sequence[str],
) -> None:
    # get local timezone
    naive = datetime.now()
    if round_:
        naive = _round_to(naive, round_)

    aware = naive.astimezone()
    local_tz = aware.tzinfo
    assert local_tz is not None, "failed to get local timezone"

    # get list of all timezones
    picked: List[zoneinfo.ZoneInfo] = (
        [_parse_timezone(_tz) for _tz in tz] if tz else [_pick_timezone()]
    )
    if not picked:
        click.echo("No timezone selected", err=True)
        return

    dates = [
        *([aware] if print_local else []),
        *(naive.astimezone(p) for p in picked),
    ]

    # get the first datetime (may be yours, else it is used as the 'first' timezone)
    first = dates[0]
    # get the difference in hours between the two timezones
    diffs = [
        (_make_unaware(dt) - _make_unaware(first)).total_seconds() / 3600
        for dt in dates
    ]

    if hours_:
        # get the date in the first timezone
        rows: List[List[Any]] = []
        # get the hours in the first timezone
        for dt, df in zip(dates, diffs):
            row: List[Any] = []
            if print_tz:
                row.append(dt.tzinfo)
                row.append(f"({_display_timezone_diff(df)})")
                row.append(first.strftime("[%b %d]"))
            for hr in range(hours_):
                shifted_dt = dt + timedelta(hours=hr)
                if shifted_dt.minute == 0:
                    row.append(shifted_dt.strftime("%H"))
                else:
                    row.append(shifted_dt.strftime("%H:%M"))
            rows.append(row)

        click.echo(tabulate(rows, headers=(), tablefmt="plain", disable_numparse=True))

    else:
        rows = []

        for d, df in zip(dates, diffs):
            if print_tz:
                rows.append([d.tzinfo, df, d.strftime(format_)])
            else:
                rows.append([d.strftime(format_)])

        click.echo(tabulate(rows, headers=(), tablefmt="plain", disable_numparse=True))


@main.command(short_help="list all timezones", name="list-tzs")
def _list_timezones() -> None:
    for tz in zoneinfo.available_timezones():
        click.echo(tz)


if __name__ == "__main__":
    main(prog_name="time-in")
