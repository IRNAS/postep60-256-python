#!/usr/bin/python3

"""
Postep256 test program

"""
import time
import logging
import signal

import postep256


# Gracefull kill for postep testing (so motor doesn't keep running after code exits)
class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        # signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        print("EXITING GRACEFULLY AFTER THIS TEST LOOP FINISHES")
        self.kill_now = True


if __name__ == '__main__':
    # set requested, speed
    # read if it was set
    # read position of motor,
    # read again -> is it changing?
    # if it didnt change, print something (and exit?)

    logging.basicConfig(filename="test.log", format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
    # logging.getLogger().addHandler(logging.StreamHandler())  # uncomment this to get test logs into console as well

    gk = GracefulKiller()

    flipflop = 1
    SPEED = 15360

    # driver init:
    address = 0x0a
    motor_driver = postep256.PoStep256(address)
    motor_driver.set_run_sleep_mode(postep256.DRIVER_SLEEP)

    while not gk.kill_now:
        # emulate 3 possible scenarios from set_motor_state:
        logging.info("---------------NEW ITERATION---------------")
        logging.info("-----(Set state to 1 or -1: motor run)-----")

        ret_mode = motor_driver.read_driver_mode()
        if ret_mode is None:
            logging.error("read_driver_mode failed")
        else:
            logging.info("read_driver_mode success: {}".format(ret_mode))

        if ret_mode != postep256.MODE_AUTO:
            ret_val = motor_driver.set_driver_mode(postep256.MODE_AUTO)
            if not ret_val:
                logging.error("set_driver_mode failed")
            else:
                logging.info("set_driver_mode success: {}".format(ret_val))

        # set motor speed to configured and read it back to confirm
        ret_speed = motor_driver.set_requested_speed(SPEED)
        if not ret_speed:
            logging.error("set_requested_speed failed")
        else:
            logging.info("set_requested_speed success")

        requested_speed = motor_driver.read_requested_speed()
        if requested_speed is None:
            logging.error("read_requested_speed failed")
        elif abs(requested_speed) != SPEED:
            logging.error("read_requested_speed success, but speed is {} and not what was set ({})".format(requested_speed, SPEED))
        else:
            logging.info("read_requested_speed success: {}".format(requested_speed))

        # set invert direction
        ret_dir = motor_driver.set_invert_direction(flipflop)
        if not ret_dir:
            logging.error("set_invert_direction failed")
        else:
            logging.info("set_invert_direction success")

        # read invert direction to confirm that it is set correctly
        invert = motor_driver.read_auto_run_invert_direction_status()
        if invert is None:
            logging.error("read_auto_run_invert_direction_status failed")
        elif invert != flipflop:
            logging.error("read_auto_run_invert_direction_status success, but value {} is not what it was set to ({})".format(invert, flipflop))

        # start the motor
        ret_value = motor_driver.set_run_sleep_mode(postep256.DRIVER_RUN)
        if not ret_value:
            logging.error("set_run_sleep_mode(DRIVER_RUN) failed")
        else:
            logging.info("set_run_sleep_mode(DRIVER_RUN) success")

        # read speed to confirm that the motor is actually running
        speed_status = False
        for _ in range(5):
            actual_speed = motor_driver.read_current_speed()
            if actual_speed is not None and actual_speed != 0:
                speed_status = True
                break
            time.sleep(0.01)
        if not speed_status:
            logging.error("Motor ISN'T actually running")
        else:
            logging.info("Motor IS actually running")

        # flip the flop
        flipflop = 0 if flipflop else 1

        # wait a bit
        time.sleep(2)

        logging.info("--------(Set state to 0: motor stop)--------")

        # stop the motor
        ret_value = motor_driver.set_run_sleep_mode(postep256.DRIVER_SLEEP)
        if not ret_value:
            logging.error("set_run_sleep_mode(DRIVER_SLEEP) failed")
        else:
            logging.info("set_run_sleep_mode(DRIVER_SLEEP) success")

        # read speed to confirm that the motor actually stopped
        speed_status = False
        for _ in range(5):
            actual_speed = motor_driver.read_current_speed()
            if actual_speed is not None and actual_speed == 0:
                speed_status = True
                break
            time.sleep(0.01)
        if not speed_status:
            logging.info("Motor DIDN'T actually stop")
        else:
            logging.info("Motor DID actually stop")

        # wait a bit
        time.sleep(2)
