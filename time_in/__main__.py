from typing import List, Any, Iterator, Union, Sequence, Literal, NamedTuple, Optional

import os
import zoneinfo
from datetime import datetime, timedelta

import click
from tabulate import tabulate

from .countryinfo import iter_countries, _get_tz_from_fzf_line


@click.group(context_settings={"max_content_width": 120})
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
    return "+" if f >= 0 else ""


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


def _local_tz() -> zoneinfo.ZoneInfo:
    import tzlocal

    tz = tzlocal.get_localzone_name()
    return _parse_timezone(tz)


class TZWithName(NamedTuple):
    tz: zoneinfo.ZoneInfo
    name: Optional[str]

    @classmethod
    def from_str(cls, s: str) -> "TZWithName":
        if ":" in s:
            name, tz = s.split(":", 1)
            return cls(_parse_timezone(tz.strip()), name.strip())
        else:
            return cls(_parse_timezone(s), None)


def _parse_dates(context: click.Context, param: Any, value: str) -> datetime:
    if value == "now":
        return datetime.now()
    else:
        import warnings
        import dateparser

        warnings.filterwarnings("ignore", "The localize method is no longer necessary")

        dt = dateparser.parse(value, settings={"PREFER_DATES_FROM": "future"})
        if dt is None:
            raise click.BadParameter(f"failed to parse date: {value}")
        if dt.tzinfo is None:
            # if the timezone is not specified, assume it's local
            dt = dt.astimezone()
        # then, convert to naive datetime
        return datetime.fromtimestamp(dt.timestamp())


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
    default=None,
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
    "-d",
    "--date",
    "date_",
    type=click.UNPROCESSED,
    default="now",
    help="date to print",
    show_default=True,
    callback=_parse_dates,
)
@click.option(
    "-P",
    "--print-local-timezone",
    "print_local_timezone",
    is_flag=True,
    help="print the local timezone name as well",
)
@click.option(
    "-r",
    "--round",
    "round_",
    type=click.Choice(["up", "down", "nearest"]),
    default=None,
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
    date_: datetime,
    print_local: bool,
    print_local_timezone: bool,
    print_tz: bool,
    round_: Optional[Literal["up", "down", "nearest"]],
    tz: Sequence[str],
) -> None:
    if hours_ and hours_ < 1:
        raise click.BadParameter("hours must be >= 1")

    # get local timezone
    if round_:
        date_ = _round_to(date_, round_)

    aware = date_.astimezone()
    local_tz = aware.tzinfo
    assert local_tz is not None, "failed to get local timezone"

    # get list of all timezones
    picked: List[TZWithName] = (
        [TZWithName.from_str(_tz) for _tz in tz]
        if tz
        else [TZWithName(_pick_timezone(), None)]
    )

    assert len(picked) > 0, "no timezones selected"

    dates = [
        *([aware] if print_local else []),
        *(date_.astimezone(p.tz) for p in picked),
    ]

    tznames: List[str] = []
    if print_local:
        if print_local_timezone:
            tznames.append(str(_local_tz()))
        else:
            tznames.append(os.environ.get("TIME-IN-LOCAL-STR", "Here"))
    tznames.extend(p.name or str(p.tz) for p in picked)

    assert len(dates) == len(tznames), "mismatched dates and timezones"

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
        for dt, df, tzn in zip(dates, diffs, tznames):
            row: List[Any] = []
            if print_tz:
                row.append(tzn)
                row.append(f"({_display_timezone_diff(df)})")
                row.append(dt.strftime("[%b %d]"))
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

        for d, df, tzn in zip(dates, diffs, tznames):
            if print_tz:
                rows.append(
                    [tzn, f"({_display_timezone_diff(df)})", d.strftime(format_)]
                )
            else:
                rows.append([d.strftime(format_)])

        click.echo(tabulate(rows, headers=(), tablefmt="plain", disable_numparse=True))


@main.command(short_help="list all timezones", name="list-tzs")
def _list_timezones() -> None:
    for tz in zoneinfo.available_timezones():
        click.echo(tz)


if __name__ == "__main__":
    main(prog_name="time-in")
