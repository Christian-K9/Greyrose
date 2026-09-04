import logging
import sys

#arguments:
#       1. Time Created: %(asctime)
#       2. Level of message: %(levelname)s
#       3. Message
if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, filename="windows.log", filemode="w",
                format="%(asctime)s - %(levelname)s - %(message)s")
    
    with open('alerts.log', 'r') as file:
        for line in file:
            level = logging.INFO
            user, source_address, host, level, message = line.split()
            logging.log(level, message)