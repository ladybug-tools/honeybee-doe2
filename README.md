# honeybee-doe2

![Honeybee](https://www.ladybug.tools/assets/img/honeybee.png) ![DOE-2](https://www.doe2.com/BldgDOE2.gif)

[![Build Status](https://github.com/ladybug-tools/honeybee-doe2/workflows/CI/badge.svg)](https://github.com/ladybug-tools/honeybee-doe2/actions)
[![Python 3.10](https://img.shields.io/badge/python-3.10-orange.svg)](https://www.python.org/downloads/release/python-3100/)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Python 2.7](https://img.shields.io/badge/python-2.7-green.svg)](https://www.python.org/downloads/release/python-270/)
[![IronPython](https://img.shields.io/badge/ironpython-2.7-red.svg)](https://github.com/IronLanguages/ironpython2/releases/tag/ipy-2.7.8/)

Honeybee extension for energy modeling with the DOE-2 engine.

[DOE-2](https://www.doe2.com/) is a widely used and accepted freeware building energy analysis program that can predict the energy use and cost for all types of buildings.

## Installation

`pip install -U honeybe-doe2`

## QuickStart

```console
import honeybee_doe2
```

## [API Documentation](http://ladybug-tools.github.io/honeybee-doe2/docs)

## Local Development

1. Clone this repo locally
```console
git clone git@github.com:ladybug-tools/honeybee-doe2

# or

git clone https://github.com/ladybug-tools/honeybee-doe2
```
2. Install dependencies:
```
cd honeybee-doe2
pip install -r dev-requirements.txt
pip install -r requirements.txt
```

3. Run Tests:
```console
python -m pytest tests/
```

4. Generate Documentation:
```console
sphinx-apidoc -f -e -d 4 -o ./docs ./honeybee_doe2
sphinx-build -b html ./docs ./docs/_build/docs
```