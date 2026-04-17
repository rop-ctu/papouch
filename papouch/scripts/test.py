import logging
import argparse
from papouch import QuidoError
from papouch.scripts.common import create_quido
from .common import add_connection_arguments
import time


def parse_cmdl_arguments():
    """
    Parses command line arguments for the quido_test application.
    """
    # Create the ArgumentParser object
    parser = argparse.ArgumentParser("quido-test")

    add_connection_arguments(parser)

    parser.add_argument("-i", "--inputs", type=int, default=4, help="Number of inputs [default: 4]")
    parser.add_argument("-o", "--outputs", type=int, default=4, help="Number of outputs [default: 4]")

    # Debug flag
    parser.add_argument("--debug", action="store_true", help="Enable debugging")

    # Parse the arguments
    args = parser.parse_args()
    return args


def main():
    args = parse_cmdl_arguments()

    if args.debug:
        logging.basicConfig(level='DEBUG')
    else:
        logging.basicConfig(level='INFO')


    q = create_quido(args)
    name = q.get_name()

    print("Name:           ", name[0])
    print("Version:        ", name[1])
    try:
        print("Temperature(1): ", q.get_temperature(1), 'C')
    except QuidoError as e:
        print(e)
    print()
    for i in range(args.inputs):
        val = q.get_input(i+1)
        print("Input({}):        {}".format(i+1, val))

    for i in range(args.outputs):
        print(f"Output({i+1}):        True")
        q.set_output(i+1, True)
        time.sleep(0.5)
        print(f"Output({i+1}):        False")
        q.set_output(i+1, False)


    print()
    print("Setting all outputs to HIGH for 1 s")
    for i in range(args.outputs):
        q.set_output(i+1, True, 1)


if __name__ == "__main__":
    main()
