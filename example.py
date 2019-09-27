"""
Postep256 Driver basic usage example
"""

import time

import postep256


def example():
    # initialize driver
    i2c_address = 0x0b  # configure this via the Postep256 USB utility
    motor_driver = postep256.PoStep256(i2c_address)

    # test if driver is responsive
    if motor_driver.loopback_read():
        print("Driver is responsive")
    else:
        print("Driver not responsive")
        return

    # Put driver to MODE_AUTO to enable basic usage
    motor_driver.set_driver_mode(postep256.MODE_AUTO)

    # Put driver/motor to sleep mode when not in use
    motor_driver.set_run_sleep_mode(postep256.DRIVER_SLEEP)  # returns False on failure

    # Set motor speed (in steps/s)
    motor_driver.set_requested_speed(1000)

    # Set motor direction
    motor_driver.set_invert_direction(0)

    # Reset position register
    motor_driver.set_zero()

    # turn the motor on (it starts spinning)
    motor_driver.set_run_sleep_mode(postep256.DRIVER_RUN)

    # wait 2 seconds
    time.sleep(2)

    # read position of motor
    position = motor_driver.read_position()
    print("Motor is at position: {}".format(position))  # position should be around speed * 2 = 2000

    # stop motor
    # motor_driver.stop()
    motor_driver.set_run_sleep_mode(postep256.DRIVER_SLEEP)

    # invert direction
    motor_driver.set_invert_direction(1)

    # wait 1 seconds
    time.sleep(1)

    # turn on motor
    motor_driver.set_run_sleep_mode(postep256.DRIVER_RUN)

    # wait 3 seconds
    time.sleep(3)

    # read position
    position = motor_driver.read_position()
    print("Motor is at position: {}".format(position))  # since we did not reset the position, it should be around -1000

    # stop motor
    motor_driver.stop()
    motor_driver.set_run_sleep_mode(postep256.DRIVER_SLEEP)


if __name__ == '__main__':
    example()
