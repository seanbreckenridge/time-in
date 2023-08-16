# time-in

CLI tool to figure out the time somewhere else

## Installation

Requires `python3.9+`

To install with pip, run:

```
pip install time-in
```

## Usage

```
time-in tz --help
```

If no timezone is passed, this uses [fzf](https://github.com/junegunn/fzf) to let you select a timezone from a list of all timezones/common countries/capitals.

![fzf example](https://github.com/seanbreckenridge/time-in/blob/main/.github/fzf.png?raw=true)

```
Usage: time-in tz [OPTIONS] [TZ]...

Options:
  -f, --format TEXT              format for printing dates  [default: %Y-%m-%d %H:%M:%S %Z]
  -h, --hours INTEGER            print this many localized hours in timezones  [default: 0]
  --print-local / --skip-local   print the local time as well
  -d, --date TEXT                date to print  [default: now]
  -P, --print-local-timezone     print the local timezone name as well
  -r, --round [up|down|nearest]  round the time to the nearest hour  [default: down]
  --print-info / --hide-info     print timezone info/difference
  --help                         Show this message and exit.
```

By default, this uses the current time, and prints the time in the timezone(s) passed.

```bash
$ time-in tz US/Eastern
Here        (+0)  2023-08-16 10:51:04 PDT
US/Eastern  (+3)  2023-08-16 13:51:04 EDT
```

If you want to print the time in the future, you can pass a date:

`$ time-in tz 'US/Eastern' --date '2023-10-16 10:30'`

or, in more human language: `$ time-in tz 'US/Eastern' --date 'in 3 hours'`

Can show multiple timezones:

```bash
$ time-in tz US/Mountain US/Central US/Eastern
Here         (+0)  2023-08-16 10:51:52 PDT
US/Mountain  (+1)  2023-08-16 11:51:52 MDT
US/Central   (+2)  2023-08-16 12:51:52 CDT
US/Eastern   (+3)  2023-08-16 13:51:52 EDT
```

To label the timezones differently, you can prepend it with a label:

```bash
$ time-in tz 'East Coast: US/Eastern' 'UK: Europe/London'
Here        (+0)  2023-08-16 10:52:04 PDT
East Coast  (+3)  2023-08-16 13:52:04 EDT
UK          (+8)  2023-08-16 18:52:04 BST
```

This can also show a range of dates, if you pass `--hours`:

```bash
$ time-in tz 'East Coast: US/Eastern' 'UK: Europe/London' --hours 12 --round down
Here        (+0)  [Aug 16]  10  11  12  13  14  15  16  17  18  19  20  21
East Coast  (+3)  [Aug 16]  13  14  15  16  17  18  19  20  21  22  23  00
UK          (+8)  [Aug 16]  18  19  20  21  22  23  00  01  02  03  04  05
```

```bash
$ time-in tz -h 6 -r down --print-local-timezone US/Eastern Europe/London Asia/Calcutta Asia/Shanghai Asia/Tokyo US/Hawaii
America/Los_Angeles  (+0)     [Aug 16]  10     11     12     13     14     15
US/Eastern           (+3)     [Aug 16]  13     14     15     16     17     18
Europe/London        (+8)     [Aug 16]  18     19     20     21     22     23
Asia/Calcutta        (+12.5)  [Aug 16]  22:30  23:30  00:30  01:30  02:30  03:30
Asia/Shanghai        (+15)    [Aug 17]  01     02     03     04     05     06
Asia/Tokyo           (+16)    [Aug 17]  02     03     04     05     06     07
US/Hawaii            (-3)     [Aug 16]  07     08     09     10     11     12
```

### Tests

```bash
git clone 'https://github.com/seanbreckenridge/time-in'
cd ./time_in
pip install '.[testing]'
flake8 ./time_in
mypy ./time_in
```

### Attributions

- The hours format was heavily influenced by [this script](https://superuser.com/a/1397116)
- Thanks to [this gist](https://gist.github.com/mjrulesamrat/0c1f7de951d3c508fb3a20b4b0b33a98) for country/city data for timezones
