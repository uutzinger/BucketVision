#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple example of parsing arguments
"""

# import the necessary packages

import argparse

# Create arg parser
parser = argparse.ArgumentParser()

# Add OPTIONAL IP Address argument
# Specify with "py bucketvision3.py -ip <your address>"
# '10.41.83.2' is the competition address (default)
# '10.38.14.2' is typical practice field
# '10.41.83.215' EXAMPLE Junior 2 radio to PC with OutlineViewer in Server Mode
# '192.168.0.103' EXAMPLE Home network  
parser.add_argument('-ip', '--ip-address', required=False, default='10.41.83.2', 
help='IP Address for NetworkTable Server')

# Parse args early so that it responds to --help
args = vars(parser.parse_args())
    
# Get the IP address as a string
networkTableServer = args['ip_address']

print("You Entered: " + networkTableServer)