# Library for Papouch Devices

This library provide python interface for the communication with the Papouch devices, namely the Quido family of IO modules. The library supports both ETH and USB variants, the RS232 was not tested. For now the library supports just the Quido over Spinel 66 protocol.

## Tools

This is a list of tools provided with the Papouch library that demonstrate the possibilities of the library. All tools provides help with `-h` or `--help` and debug mode with `--debug`.

 - **quido-cli** Command line interface for the Quido family of devices.
 - **quido-test** Test utility for the Quido device.
 - **quido-async-test** Async USB test utility for the Quido device.
 - **quido-list** List all devices on the network segment, prints out MAC and IP addresses.

## Usage

The following is the simplest example of the library in action.

``` python
from papouch import Quido

# initialize Quido USB
q = Quido()
q.connect_usb('/dev/ttyUSB0')

# get info about the device
q.get_name() # => [u'Quido USB 4/4', u'v0253.03.35', u'f66 97', u't']

# set output
q.set_output(1, True) # => True

```

**quido-cli**

``` shell
quido-cli --conn usb:/dev/ttyUSB0 info
quido-cli --conn eth:192.168.1.254 seto 1H 2L 3T
quido-cli --conn eth:192.168.1.254 geto 1 2 3
quido-cli --conn eth:192.168.1.254 geti 1 2 3
quido-cli --conn eth:192.168.1.254 inst OR 1
```

**quido-list**

Broadcast discovery is sent across all active IPv4 interfaces automatically.

``` shell
sudo quido-list
# 01 mac: 00-1A-2B-3C-4D-5E ip: 192.168.1.123
# Found 1 devices.

sudo quido-list --interface eno1
sudo quido-list --timeout 1.5
```

``` text
$ quido-list --help
usage: quido-list [-h] [-i INTERFACE] [-t TIMEOUT]

Discover Papouch Quido devices by UDP broadcast on network interfaces.

options:
  -h, --help            show this help message and exit
  -i, --interface INTERFACE
                        Limit discovery to one network interface (for example:
                        eno1)
  -t, --timeout TIMEOUT
                        Discovery timeout in seconds [default: 3.0]

Note: discovery uses Linux raw sockets (AF_PACKET). Run as root or grant
CAP_NET_RAW (for example via sudo).
```

**quido-test**

``` shell
quido-test --usb /dev/ttyUSB0
quido-test --eth 192.168.1.254 --port 1001
```

**quido-async-test**

``` shell
quido-async-test --usb /dev/ttyUSB0
```

## Library Reference

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

## Installation

Dependencies:

 - [pyserial](https://pythonhosted.org/pyserial/)
 - [pyserial-asyncio](https://pypi.org/project/pyserial-asyncio/)
 - [requests](http://docs.python-requests.org/en/latest/)

Install for local development (editable mode):

``` shell
python -m pip install -e .
```

Install as a regular package:

``` shell
python -m pip install .
```

## ROS

In order to enable the ROS support clone this repository same as in the previous examples without using pip but inside the ROS workspace i.e:

``` shell
cs [ros/ssh] # your ros workspace
git clone http://gitlab.ciirc.cvut.cz/b635/papouch.git
cd papouch
sudo python setup.py install
catkin build
source devel/setup.sh
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
