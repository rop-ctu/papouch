
# Library for Papouch Devices

This library provide python interface for the communication with the Papouch devices, namely the Quido family of IO modules. The library supports both ETH and USB variants, the RS232 was not tested.

## Tools

This is a list of tools provided with the Papouch library that demonstrate the possibilities of the library. All tools provides help with `-h` or `--help` and debug mode with `--debug`.

 - **quido-cli** Command line interface for the Quido family of devices.
 - **quido-test** Test utility for the Quido device.

## Usage

The following is the simplest example of the library in action.

``` python
from papouch import Quido

# initialize Quido ETH
q = Quido()
q.connect_usb('/dev/ttyUSB0')

# get info about the device
q.get_name() # => [u'Quido USB 4/4', u'v0253.03.35', u'f66 97', u't']

# set output
q.set_output(1, True) # => True

```

## Reference

- `class papouch.Quido`

  - `__init__()`
  - `connect_tcp(ip, port=1001)`
  - `connect_usb(dev, baud=115200)`
  - `cmd(inst, data='', adr='$', buff=100)`
  - `reset()`
  - `get_name() => [...]`
  - `get_temperature() => float`
  - `set_output(n, state, duration=None) => bool`
  - `get_output(n) => bool`
  - `get_input(n) => bool`

- `class papouch.QuidoWeb`

  - `__init__(ip)`
  - `set_output(n, state, duration=None)`

## Instalation

Dependencies:

 - [pyserial](https://pythonhosted.org/pyserial/)
 - [requests](http://docs.python-requests.org/en/latest/)
 - [docopt](http://docopt.org/)

