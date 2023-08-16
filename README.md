# time-in

cli tool to figure out the time somewhere else

## Installation

Requires `python3.8+`

To install with pip, run:

```
pip install git+https://github.com/seanbreckenridge/time-in
```

## Usage

```
time-in --help
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

