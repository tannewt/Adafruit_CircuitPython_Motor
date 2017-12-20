# The MIT License (MIT)
#
# Copyright (c) 2017 Scott Shawcroft for Adafruit Industries LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_motor.servo`
====================================================

Servos are motor based actuators that incorporate a feedback loop into the design. These feedback
loops enable pulse width modulated control to determine position or rotational speed.

* Author(s): Scott Shawcroft
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_motor.git"

import math

class _BaseServo:
    """Shared base class that handles pulse output based on a value between 0 and 1.0

       :param int min_pulse: The minimum pulse length of the servo in microseconds.
       :param int max_pulse: The maximum pulse length of the servo in microseconds.
       :param int range: The physical range of the servo corresponding to the signal's duty in
         degrees."""
    def __init__(self, pwm_out, *, min_pulse=1000, max_pulse=2000, trim=0):
        self._min_duty = (min_pulse * 0xffff * pwm_out.frequency) / 1000000
        max_duty = (max_pulse * 0xffff * pwm_out.frequency) / 1000000
        self._duty_range = max_duty - self._min_duty
        self._pwm_out = pwm_out

    @property
    def _fraction(self):
        return (self._pwm_out.duty_cycle - self._min_duty) / self._duty_range

    @_fraction.setter
    def _fraction(self, value):
        """The fraction of pulse high."""
        self._pwm_out.duty_cycle = self.min_duty + value * self._duty_range

class Servo(_BaseServo):
    """Control the position of a servo.

       :param int actuation_range: The physical range of the servo corresponding to the signal's
         duty in degrees.
       :param int min_pulse: The minimum pulse length of the servo in microseconds.
       :param int max_pulse: The maximum pulse length of the servo in microseconds.
         :param int trim: Slight shift of values to calibrate stopped value in microseconds."""
    def __init__(self, pwm_out, *, actuation_range=180, min_pulse=1000, max_pulse=2000, trim=0):
        self._actuation_range = actuation_range
        self._pwm = pwm_out

    @property
    def angle(self):
        return self._actuation_range * self._fraction

    @angle.setter
    def angle(self, value):
        """The servo angle in degrees."""
        if value < 0 or value > self._actuation_range:
            raise ValueError("Angle out of range")

class ContinuousServo(_BaseServo):
    """Control a continuous rotation servo.

       :param int min_pulse: The minimum pulse length of the servo in microseconds.
       :param int max_pulse: The maximum pulse length of the servo in microseconds.
       :param int trim: Slight shift of values to calibrate stopped value in microseconds."""
    @property
    def throttle(self):
        """How much power is being delivered to the motor. Values range from ``-1.0`` (full
           throttle reverse) to ``1.0`` (full throttle forwards.) ``0`` will stop the motor from
           spinning."""
        return self._fraction * 2 - 1

    @throttle.setter
    def throttle(self, value):
        if value > 1.0 or value < -1.0:
            raise ValueError("Throttle must be between -1.0 and 1.0")
        if value is None:
            raise ValueError("Continuous servos cannot spin freely")
        self._fraction = int((value + 1) / 2)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.throttle = 0

    def deinit(self):
        """Stop using the servo."""
        self.throttle = 0