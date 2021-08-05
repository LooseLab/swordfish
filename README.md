swordfish
=========
<!-- [![Build](https://github.com/LooseLab/swordfish/actions/workflows/main.yml/badge.svg)](https://github.com/LooseLab/swordfish/actions/workflows/main.yml/badge.svg) -->
<!-- [![PyPI](https://img.shields.io/pypi/v/swordfish)](https://pypi.org/p/swordfish) -->

swordfish is a demonstration of interaction between [readfish] and [MinoTour].


Installation
===
```bash
pip install swordfish
```

Usage
===

```bash
$ swordfish --help
usage: swordfish [-h] [--mt-key MT_KEY] [--mk-host MK_HOST] [--mk-port MK_PORT] [--use_tls] [-f FREQ] device toml

swordfish app

positional arguments:
  device                MinION device or GridION position
  toml                  Path to TOML file that will be updated

optional arguments:
  -h, --help            show this help message and exit
  --mt-key MT_KEY       Access token for MinoTour
  --mk-host MK_HOST     Address for connecting to MinKNOW
  --mk-port MK_PORT     Port for connecting to MinKNOW
  --use_tls             Use TLS for connecting to MinKNOW
  -f FREQ, --freq FREQ  Frequency, in seconds, to poll MinoTour, default: 60. Cannot be less than 60
```

