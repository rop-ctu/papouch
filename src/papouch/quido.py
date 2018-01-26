
import requests

class Quido(object):

    HIGH = 's'
    LOW = 'r'
    TOGGLE = 'i'
    ALLHIGH = 'S'
    ALLLOW = 'R'
    
    def __init__(self, ip, nin=4, nout=4):
        """Initialize Quido module
        
        Arguments:
          ipaddr    IP address of the module

        Opional arguments:
          nin       Number of inputs
          nout      Number of outputs

        """
        self.ip = ip
        self.nin = nin
        self.nout = nout


    def cmd_output(self, ctype, oid=None):
        """
        """

        if ctype in [self.ALLLOW, self.ALLHIGH]:
            cmd = "http://{}/set.xml?type={}".format(self.ip, ctype)
        else:
            cmd = "http://{}/set.xml?type={}&id={}".format(self.ip, ctype, oid)

        # Call GET request
        r = requests.get(cmd)

        print r
