swordfish
=========
[![Build](https://github.com/LooseLab/swordfish/actions/workflows/main.yml/badge.svg)](https://github.com/LooseLab/swordfish/actions/workflows/main.yml/badge.svg)
<!-- [![PyPI](https://img.shields.io/pypi/v/swordfish)](https://pypi.org/p/swordfish) -->

swordfish is a demonstration of interaction between [readfish](https://github.com/LooseLab/readfish) and 
[MinoTour](https://github.com/LooseLab/minotourapp).


Installation
===


```bash
git clone https://github.com/LooseLab/swordfish
cd swordfish
python3 -m venv venv
. ./venv/bin/activate
pip install -U pip setuptools wheel
pip install -e .
```

Usage
===

```bash
$ swordfish --help
usage: swordfish [-h] {balance} ...

swordfish app

optional arguments:
  -h, --help  show this help message and exit

subcommands:
  {balance}   additional help
    balance   Connect to minoTour and configure a balancing experiment.
```

## Subcommands
### Balance - balance ARTIC amplicons at a given coverage

```bash 
$ swordfish balance --help
usage: swordfish balance [-h] --mt-key MT_KEY [--mk-host MK_HOST] [--mk-port MK_PORT] [--use_tls] [-f FREQ]
                         [--mt-host MT_HOST] [--mt-port MT_PORT] [--no-minknow] [--threshold THRESHOLD] --toml
                         TOML --device DEVICE

optional arguments:
  -h, --help            show this help message and exit
  --mt-key MT_KEY       Access token for MinoTour
  --mk-host MK_HOST     Address for connecting to MinKNOW
  --mk-port MK_PORT     Port for connecting to MinKNOW
  --use_tls             Use TLS for connecting to MinKNOW
  -f FREQ, --freq FREQ  Frequency, in seconds, to poll MinoTour, default: 60. Cannot be less than 60
  --mt-host MT_HOST     Address for connecting to minoTour. Default - localhost
  --mt-port MT_PORT     Port for connecting to minotour. Default - 8100.
  --no-minknow          For testing - skips minknow validation. Not recommended. Will be deprecated in favour of a
                        mock minknow server for testing.
  --threshold THRESHOLD
                        Threshold X coverage to start unblocking amplicons on a barcode. Default 50. Cannot be
                        less than 20.
  --toml TOML           Path to TOML file that will be updated
  --device DEVICE       MinION device or GridION position
```

Example command:
```bash
swordfish --mt-key <MTKEY> --device X5 --toml example.toml --mt-host minotour.nottingham.ac.uk --mk-port 9502 --mt-port 443 balance --threshold 100
```

The above command will query minoTour hosted at _minotour.nottingham.ac.uk_, using the run_id picked up from the minKNOW API for the run on gridION position X5. It will then create a TOML file called example.toml_live,
unblocking all amplicons over 100x on barcodes detected by minoTour. The TOML field must be the same as the TOML file path that readfish is using. 
