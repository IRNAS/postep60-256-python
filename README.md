# Postep256 Motor controller driver

Python driver for Polabs PoStep60-256 stepper motor driver

## Basic usage

Initialize by providing devices I2C address

```python3
i2c_address = 0x0b
motor_driver = postep256.PoStep256(i2c_address)
```

Configure for basic usage
(See [example](example.py) for more information)

```python3
motor_driver.set_driver_mode(postep256.MODE_AUTO)
motor_driver.set_run_sleep_mode(postep256.DRIVER_SLEEP)
motor_driver.set_requested_speed(1000)
motor_driver.set_invert_direction(0)
motor_driver.set_zero()
```

Turn the motor on

```python3
motor_driver.set_run_sleep_mode(postep256.DRIVER_RUN)
```

Stop the motor

```python3
motor_driver.set_run_sleep_mode(postep256.DRIVER_SLEEP)
```

Invert direction

```python3
motor_driver.motor_driver.set_invert_direction(1)
```
