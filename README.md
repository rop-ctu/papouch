
# Library for Papouch Devices

This library provide python interface for the communication with the Papouch devices, namely the Quido family of IO modules. The library supports both ETH and USB variants, the RS232 was not tested. For now the library supports just the Quido over Spinel 66 protocol.

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

  - `.__init__()`
  - `.connect_tcp(ip, port=1001)`
  - `.connect_usb(dev, baud=115200)`
  - `.cmd(inst, data='', adr='$', buff=100)`
  - `.reset()`
  - `.get_name() => [...]`
  - `.get_temperature() => float`
  - `.set_output(n, state, duration=None) => bool`
  - `.get_output(n) => bool`
  - `.get_input(n) => bool`
  - `.connection => str`
  - `.wait_for_edge(n) => bool` returns True for raising edge and False for falling edge for given input.

- `class papouch.QuidoWeb`

  - `__init__(ip)`
  - `set_output(n, state, duration=None)`

## Instalation

Dependencies:

 - [pyserial](https://pythonhosted.org/pyserial/)
 - [requests](http://docs.python-requests.org/en/latest/)
 - [docopt](http://docopt.org/)

Install with pip

``` shell
pip install git+http://gitlab.ciirc.cvut.cz/b635/papouch.git
```

or without pip

``` shell
git clone http://gitlab.ciirc.cvut.cz/b635/papouch.git
cd papouch
python setup.py install
```

or

``` shell
git clone git@gitlab.ciirc.cvut.cz:b635/papouch.git
cd papouch
python setup.py install
```

## ROS

In order to enable the ROS support clone this repository same as in the previous examples without using pip but inside the ROS workspace i.e:

``` shell
cs [ros/ssh] # your ros workspace
git clone http://gitlab.ciirc.cvut.cz/b635/papouch.git
cd papouch
python setup.py install
```

Then do the `catkin build` as normal in order to register the package. The ros node is then started with:

``` shell
rosrun papouch_ros quido_node --dev /dev/ttyACM0
```

Note that the quido device may appear under different name than `/dev/ttyACM0`. If you are using ETH version of the quido use the following command instead:

``` shell
rosrun papouch_ros quido_node --eth 192.168.1.2
```

Providing appropriate IP address of the device. The node then provides the following services:

- `~write_io` with the service description [papouch_ros/WriteIO](papouch_ros/srv/WriteIO.srv). Use to write outputs of the quido module. Multiple outputs can be written using single request.
