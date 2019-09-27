"""
PoStep256 driver, PoLabs
Motor controller for bipolar stepper motor or two brushed DC motors
I2C protocol
Manual: PoStep User Manual 2019-05-31.pdf
"""
import smbus
import struct
import logging

# selected i2c channel on rpi
I2C_CHANNEL = 1

# variables upper limits
MAX_TEMP = 120      # C
MAX_CURRENT = 6.0   # A
MAX_SPEED = 60000   # steps
MAX_ACCELERATION = 50000    # steps
MAX_BUFFER_LENGTH = 5   # max buffer size is 40 bits (5 bytes)

# driver states
DRIVER_RUN = 0xda
DRIVER_SLEEP = 0x0f

# driver modes
MODE_DEFAULT = 0x01
MODE_POSITION_CONT = 0x04
MODE_BINX_BUTTONS = 0x05
MODE_AUTO = 0x06


class PoStep256(object):
    def __init__(self, address):
        """Init smbus channel and Pca9554 driver on specified address."""
        try:
            self.i2c_bus = smbus.SMBus(I2C_CHANNEL)
            self.i2c_address = address
            # test connection to device
            if not self.loopback_read():
                raise ValueError
        except ValueError:
            logging.error("No driver found on specified address or driver communication error!")
            self.i2c_bus = None
        except:
            logging.error("Bus on channel {} is not available.".format(I2C_CHANNEL))
            logging.info("Available busses are listed as /dev/i2c*")
            self.i2c_bus = None

    def write_data(self, register, buffer=[]):
        """Write i2c block data from buffer to device, into specified register. Returns True if successful."""
        try:
            if register < 0x01 or register > 0x60:
                return False
            if not type(buffer) is list:
                buffer = [buffer]
            self.i2c_bus.write_i2c_block_data(self.i2c_address, register, buffer)
            return True
        except Exception as e:
            print("Postep256 - write i2c data error: {}".format(e))
            return False

    def read_data(self, register, length=None):
        """Read i2c block data from devices specified register into buffer to return, optional: length is num of bytes to read. Returns -1 if unsuccessful."""
        try:
            if register < 0x01 or register > 0x60:
                return None
            if length < 1 or length > MAX_BUFFER_LENGTH:
                return None

            if length:
                buffer = self.i2c_bus.read_i2c_block_data(self.i2c_address, register, length)
            else:
                buffer = self.i2c_bus.read_i2c_block_data(self.i2c_address, register)
            return buffer
        except Exception as e:
            print("Postep256 - read i2c data error: {}".format(e))
            return None

    def convert_to_byte_buffer(self, value):
        """Convert number to byte list with elements from msb to lsb."""
        if value <= 255:    # biggest num to fit in a byte
            return [value]
        elif value <= 65535:
            msb = value >> 8
            lsb = value & 0xff
            return [msb, lsb]
        elif value <= 4294967295:
            msb = value >> 8 * 3
            remain1 = value & 0xffffff
            mid1 = remain1 >> 8 * 2
            remain2 = value & 0xffff
            mid2 = remain2 >> 8
            lsb = value & 0xff
            return [msb, mid1, mid2, lsb]
        else:
            return []

    def read_value(self, register):
        """Read one byte from specified register.. Returns -1 if unsuccessful."""
        write_res = self.write_data(register)
        if not write_res:
            return None
        buffer = self.read_data(register, 1)
        if type(buffer) is list:
            buffer = buffer[0]
        return buffer

    def loopback_read(self):
        """Test a response of PoStep driver, send 4 bytes to register 0x01, should read them back. Returns True if successful."""
        try:
            buff = [0x91, 0x92, 0x93, 0x94]
            write_res = self.write_data(0x01, buff)
            if not write_res:
                return False
            returned = self.read_data(0x01, len(buff) + 1)
            returned_buff = returned[1:]    # first byte is address num, so ignore it
            if returned_buff == buff:
                return True
            else:
                return False
        except:
            return False

    def set_run_sleep_mode(self, value):
        """Enable=DRIVER_RUN or disable=DRIVER_SLEEP the driver, register: 0x03, one byte of data. Returns True if successful."""
        if value == DRIVER_SLEEP:
            result = self.write_data(0x03, value)
            return result
        elif value == DRIVER_RUN:
            result = self.write_data(0x03, value)
            return result
        else:   # wrong value
            return False

    def set_address(self, cur, new):
        """Change devices i2c address, from cur=current to new=desired, register: 0x04. Returns True if successful. """
        # check if both addresses are valid and not the same
        if cur == new:
            return True
        if cur < 0x01 or cur > 0x7f:
            return False
        if new < 0x01 or new > 0x7f:
            return False
        result = self.write_data(0x04, [cur, new])
        return result

    def set_driver_mode(self, value):
        """Set driver mode, 1=default or 6=auto, register: 0x05, performs stop and set_zero before changing. Returns True if successful."""
        # request stop and zero before changing driver mode
        self.stop()
        self.set_zero()

        # allow changing mode even if request stop and set zero have failed
        if value == MODE_AUTO or value == MODE_DEFAULT:
            result = self.write_data(0x05, value)
            return result
        else:
            return False

    def set_pwm_motors(self, motor1_freq, motor2_freq, motor1_duty_ccw, motor1_duty_acw, motor2_duty_ccw, motor2_duty_acw):
        """Set PWM in DC motor control mode, register: 0x06, write 6 bytes. . Returns True if successful. NOTE: First set driver to DC motor control mode via USB!"""
        result = self.write_data(0x06, [motor1_freq, motor2_freq, motor1_duty_ccw, motor1_duty_acw, motor2_duty_ccw, motor2_duty_acw])
        return result

    def read_hw_fw_info(self):
        """Read driver info, register: 0x0a, get 5 bytes: 0=driverID, 1=hw_major, 2=hw_minor, 3=fw_major, 4=fw_minor."""
        write_res = self.write_data(0x0a)
        if not write_res:
            return None
        buffer = self.read_data(0x0a, 5)
        return buffer

    def read_voltage(self):
        """Read PoStep supply voltage, register: 0x10, returns calculated voltage in V."""
        write_res = self.write_data(0x10)
        if not write_res:
            return None
        buffer = self.read_data(0x10, 2)
        tuple_buff = struct.unpack('h', bytes(buffer))
        calculated = tuple_buff[0] * 0.072
        return calculated

    def read_temperature(self):
        """Read PoStep temperature, register: 0x11, returns calculated temperature in C."""
        write_res = self.write_data(0x11)
        if not write_res:
            return None
        buffer = self.read_data(0x11, 2)
        tuple_buff = struct.unpack('h', bytes(buffer))
        calculated = tuple_buff[0] * 0.125
        return calculated

    def read_pin_statuses(self):
        """Read pin statutes, register: 0x12, returns a byte, where each bit represents one pin (0=low or 1=high)."""
        return self.read_value(0x12)

    def read_driver_status(self):
        """Read driver status, register: 0x13, returns numerical value."""
        return self.read_value(0x13)

    def read_driver_mode(self):
        """Read driver mode, register: 0x14, returns numerical value."""
        return self.read_value(0x14)

    def read_current(self, register):
        """Read current in specified register, NOTE: not to be used directly."""
        write_res = self.write_data(register)
        if not write_res:
            return None
        buffer = self.read_data(register, 2)
        calculated = 0.065 * buffer[0] / (2 ** buffer[1])
        return calculated

    def read_current_full_scale(self):
        """Read full scale current, register: 0x20, returns calculated current in A."""
        return self.read_current(0x20)

    def read_current_idle(self):
        """Read idle current, register: 0x21, returns calculated current in A."""
        return self.read_current(0x21)

    def read_current_overheat(self):
        """Read overheat current, register: 0x22, returns calculated current in A."""
        return self.read_current(0x22)

    def read_step_mode(self):
        """Read step mode, register: 0x23, returns mode value."""
        buffer = self.read_value(0x23)
        converted = buffer & 0x0f
        return converted

    def read_temperature_limit(self):
        """Read temperature limit, register: 0x24, returns calulated temperature in C."""
        return self.read_value(0x24)

    def read_faults(self):
        """Read faults, register: 0x25, returns 1 byte, where each bit represents one fault if set to 1."""
        return self.read_value(0x25)

    def set_current(self, register, value):
        """Set current in specified register, NOTE: not to be used directly. Returns True if successful."""
        tq = int(123 * value)
        ai = 3
        while tq > 255:
            ai -= 1
            tq = tq >> 1
        result = self.write_data(register, [tq, ai])
        return result

    def set_current_full_scale(self, value):
        """Set full scale current, parameter value in A: 2 bytes size, gets auto calculated, register 0x30. Returns True if successful."""
        if value < 0.0 or value > MAX_CURRENT:
            return False
        return self.set_current(0x30, value)

    def set_current_idle(self, value):
        """Set idle current, parameter value in A: 2 bytes size, gets auto calculated, register 0x31. Returns True if successful."""
        if value < 0.0 or value > MAX_CURRENT:
            return False
        return self.set_current(0x31, value)

    def set_current_overheat(self, value):
        """Set overheat current, parameter value in A: 2 bytes size, gets auto calculated, register 0x32. Returns True if successful."""
        if value < 0.0 or value > MAX_CURRENT:
            return False
        return self.set_current(0x32, value)

    def set_step_mode(self, value):
        """Set step mode, parameter value=int(0-8), size 1 byte, register: 0x33. Returns True if successful."""
        if value < 0 or value > 8:
            return False
        result = self.write_data(0x33, value)
        return result

    def set_temperature_limit(self, value):
        """Set temperature limit, parameter value=int(0-120 C), size 1 byte, register: 0x34. Returns True if successful."""
        if value < 0 or value > MAX_TEMP:
            return False
        result = self.write_data(0x34, value)
        return result

    def reset_faults(self):
        """Reset all faults, register: 0x35. Returns True if successful."""
        result = self.write_data(0x35)
        return result

    def write_settings_to_eeprom(self):
        """Store changes made with any of the set commands, register: 0x3f. Returns True if successful."""
        result = self.write_data(0x3f)
        return result

    # ------------------ Following commands are related to internal position controller ------------------

    def read_position(self):
        """Read position, register: 0x40, returns calculated position in steps."""
        write_res = self.write_data(0x40)
        if not write_res:
            return None
        buffer = self.read_data(0x40, 4)
        calculated = struct.unpack('i', bytes(buffer))
        return calculated[0]    # return first number from tuple

    def read_speed(self, register):
        """Read speed specified by register, NOTE: not to be used directly."""
        write_res = self.write_data(register)
        if not write_res:
            return None
        buffer = self.read_data(register, 2)
        calculated = struct.unpack('h', bytes(buffer))
        return calculated[0]    # return first number from tuple

    def read_max_speed(self):
        """Read maximum speed, register: 0x41, returns calculated speed in steps/s."""
        return self.read_speed(0x41)

    def read_acceleration(self):
        """Read acceleration, register: 0x42, returns acceleration in steps/s^2."""
        return self.read_speed(0x42)

    def read_deceleration(self):
        """Read deceleration, register: 0x43, returns deceleration in steps/s^2."""
        return self.read_speed(0x43)

    def read_current_speed(self):
        """Read current speed, register: 0x44, returns calculated speed in steps/s."""
        return self.read_speed(0x44)

    def read_requested_speed(self):
        """Read requested speed, register: 0x45, returns calculated speed in steps/s."""
        return self.read_speed(0x45)

    def read_auto_run_invert_direction_status(self):
        """Read PoStep auto run invert direction status, register: 0x46, returns direction (0 or 1)."""
        return self.read_value(0x46)

    def set_position(self, value):
        """Set position, parameter value: 4 bytes, register: 0x50. Returns True if successful. NOTE: Driver must be in POSITION_CONTROL or BINX_BUTTONS mode (set via USB)!"""
        cur_mode = self.read_driver_mode()
        if cur_mode != MODE_POSITION_CONT and cur_mode != MODE_BINX_BUTTONS:
            return False
        buffer = self.convert_to_byte_buffer(value)
        buffer.reverse()
        while len(buffer) < 4:
            buffer.append(0)
        result = self.write_data(0x50, buffer)
        return result

    def set_speed(self, register, value):
        """Set motor to specific speed specified by register to value. Returns True if successful. NOTE: not to be used directly."""
        buff = self.convert_to_byte_buffer(value)
        if not buff:
            return False
        if len(buff) == 1:
            buff.append(0)
            new_buff = buff
        else:
            new_buff = [buff[1], buff[0]]
        result = self.write_data(register, new_buff)
        return result

    def set_max_speed(self, value):
        """Set maximum speed, parameter value in steps/s, size: 2 bytes, register: 0x51. Returns True if successful."""
        if value < 0 or value > MAX_SPEED:
            return False
        return self.set_speed(0x51, value)

    def set_acceleration(self, value):
        """Set acceleration, parameter value in steps/s^2, size: 2 bytes, register: 0x52. Returns True if successful."""
        if value < 0 or value > MAX_ACCELERATION:
            return False
        return self.set_speed(0x52, value)

    def set_deceleration(self, value):
        """Set deceleration, parameter value in steps/s^2, size: 2 bytes, register: 0x53. Returns True if successful."""
        if value < 0 or value > MAX_ACCELERATION:
            return False
        return self.set_speed(0x53, value)

    def set_requested_speed(self, value):
        """Set requested speed, parameter value=int in steps/s, size: 2 bytes, register: 0x54 """
        cur_mode = self.read_driver_mode()  # check if driver is in MODE_AUTO
        if cur_mode != MODE_AUTO:
            return False
        if value < 0 or value > MAX_SPEED:
            return False
        return self.set_speed(0x54, value)

    def set_invert_direction(self, value):
        """Set invert direction, parameter value, 1 byte: LSB bit only (0 or 1), register: 0x55 """
        cur_mode = self.read_driver_mode()  # check if driver is in MODE_AUTO
        if cur_mode != MODE_AUTO:
            return False
        if value < 0 or value > 1:
            return False

        buff = self.convert_to_byte_buffer(value)
        if not buff:
            return False
        result = self.write_data(0x55, buff)
        return result

    def set_zero(self):
        """Set driver to zero, register: 0x5e. Returns True if successful."""
        result = self.write_data(0x5e)
        return result

    def stop(self):
        """Perform stop, register: 0x5f. Returns True if successful."""
        result = self.write_data(0x5f)
        return result

    def system_reset(self):
        """Perform system reset, register: 0x60. Returns True if successful."""
        result = self.write_data(0x60)
        return result

    def __del__(self):
        """Driver destructor."""
        self.i2c_bus = None
