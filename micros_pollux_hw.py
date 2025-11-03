from ScopeFoundry import HardwareComponent
import threading
import time
from qtpy import QtCore

try:
    from .micros_venus_stage import PolluxVenusStageController
except Exception as err:
    print("Cannot load required modules for Micros Pollux stage:", err)


class MicrosPolluxStageHW(HardwareComponent):

    name = 'micros_pollux_stage'

    def __init__(self, app, debug=False, name=None,
                 x_axis=0, y_axis=1,
                 invert_x=False, invert_y=False):
        """
        Initialize Micros Pollux Stage Hardware Component.

        Args:
            app: ScopeFoundry App instance
            debug: Enable debug mode
            name: Custom name for the hardware component
            x_axis: Axis number for X (default: 0)
            y_axis: Axis number for Y (default: 1)
            invert_x: Invert X axis direction
            invert_y: Invert Y axis direction
        """
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.invert_x = invert_x
        self.invert_y = invert_y

        HardwareComponent.__init__(self, app, debug=debug, name=name)

    def setup(self):
        """Setup settings and operations for the hardware component."""

        # Position settings (read-only, updated by hardware)
        xy_kwargs = dict(
            initial=0.0,
            dtype=float,
            unit='mm',
            spinbox_decimals=5,
            spinbox_step=0.1
        )

        self.settings.New('x_position', ro=True, **xy_kwargs)
        self.settings.New('y_position', ro=True, **xy_kwargs)

        # Movement status (read-only)
        self.settings.New('x_moving', dtype=bool, ro=True, initial=False)
        self.settings.New('y_moving', dtype=bool, ro=True, initial=False)

        # Target position settings (writable)
        self.settings.New('x_target', ro=False, **xy_kwargs)
        self.settings.New('y_target', ro=False, **xy_kwargs)

        # Velocity settings (mm/s or units/s depending on stage configuration)
        self.settings.New("velocity_x", ro=False, initial=1000.0,
                         unit='units/s', spinbox_decimals=1,
                         spinbox_step=100.0, vmin=0.0, vmax=10000.0)
        self.settings.New("velocity_y", ro=False, initial=1000.0,
                         unit='units/s', spinbox_decimals=1,
                         spinbox_step=100.0, vmin=0.0, vmax=10000.0)

        # Acceleration settings (units/s^2)
        self.settings.New("acceleration_x", ro=False, initial=500.0,
                         unit='units/s²', spinbox_decimals=1,
                         spinbox_step=50.0, vmin=0.0, vmax=5000.0)
        self.settings.New("acceleration_y", ro=False, initial=500.0,
                         unit='units/s²', spinbox_decimals=1,
                         spinbox_step=50.0, vmin=0.0, vmax=5000.0)

        # Deceleration settings (units/s^2)
        self.settings.New("deceleration_x", ro=False, initial=500.0,
                         unit='units/s²', spinbox_decimals=1,
                         spinbox_step=50.0, vmin=0.0, vmax=5000.0)
        self.settings.New("deceleration_y", ro=False, initial=500.0,
                         unit='units/s²', spinbox_decimals=1,
                         spinbox_step=50.0, vmin=0.0, vmax=5000.0)

        # Serial port settings
        self.settings.New('port', dtype=str, initial='COM3')
        self.settings.New('baudrate', dtype=int, initial=19260)

        # Add operations
        self.add_operation("Halt XY", self.halt_xy)
        self.add_operation("Calibrate X", self.calibrate_x)
        self.add_operation("Calibrate Y", self.calibrate_y)
        self.add_operation("Calibrate XY", self.calibrate_xy)

        # Update timer for reading positions
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.on_update_timer)
        # Timer will be started in connect() method

    def connect(self):
        """Connect to the Pollux stage controller."""
        S = self.settings

        # Open connection to hardware
        self.stage = PolluxVenusStageController(
            port=S['port'],
            baudrate=S['baudrate'],
            timeout=1.0,
            debug=self.settings['debug_mode']
        )

        # Connect position logged quantities (read-only)
        S.x_position.connect_to_hardware(read_func=self.read_pos_x)
        S.y_position.connect_to_hardware(read_func=self.read_pos_y)

        # Connect movement status logged quantities (read-only)
        S.x_moving.connect_to_hardware(read_func=self.read_x_moving)
        S.y_moving.connect_to_hardware(read_func=self.read_y_moving)

        # Connect debug mode
        def set_debug_mode(val):
            # Venus stage doesn't have debug mode in the class,
            # but we can add it if needed
            pass
        S.debug_mode.connect_to_hardware(write_func=set_debug_mode)

        # Read initial positions
        try:
            S.x_position.read_from_hardware()
            S.y_position.read_from_hardware()
        except Exception as err:
            print('Cannot read XY position:', err)

        # Set initial target to current position
        S['x_target'] = S['x_position']
        S['y_target'] = S['y_position']

        # Connect target positions (writable)
        S.x_target.connect_to_hardware(write_func=self.move_x)
        S.y_target.connect_to_hardware(write_func=self.move_y)

        # Connect velocity settings
        S.velocity_x.connect_to_hardware(write_func=self.set_velocity_x)
        S.velocity_y.connect_to_hardware(write_func=self.set_velocity_y)
        S.velocity_x.write_to_hardware()
        S.velocity_y.write_to_hardware()

        # Connect acceleration settings
        S.acceleration_x.connect_to_hardware(write_func=self.set_acceleration_x)
        S.acceleration_y.connect_to_hardware(write_func=self.set_acceleration_y)
        S.acceleration_x.write_to_hardware()
        S.acceleration_y.write_to_hardware()

        # Connect deceleration settings
        S.deceleration_x.connect_to_hardware(write_func=self.set_deceleration_x)
        S.deceleration_y.connect_to_hardware(write_func=self.set_deceleration_y)
        S.deceleration_x.write_to_hardware()
        S.deceleration_y.write_to_hardware()

        # Flag to track if other observers are reading position
        self.other_observer = False

        # Start the update timer
        self.update_timer.start(1000)

        self._is_connected = True

    def disconnect(self):
        """Disconnect from the Pollux stage controller."""

        self.update_timer.stop()

        # Disconnect all settings from hardware
        self.settings.disconnect_all_from_hardware()

        # Close the stage connection
        if hasattr(self, 'stage'):

            self.stage.close()
            del self.stage

        self._is_connected = False

    def on_update_timer(self):
        """Periodic update of position and moving status readings."""
        if self.settings['connected']:
            try:
                self.settings.x_position.read_from_hardware()
                self.settings.y_position.read_from_hardware()
                self.settings.x_moving.read_from_hardware()
                self.settings.y_moving.read_from_hardware()
            except Exception as err:
                if self.settings['debug_mode']:
                    print(f"Error reading position/status: {err}")

            # Adjust timer interval based on whether other observers are active
            if self.other_observer:
                self.update_timer.setInterval(2000)
            elif (self.settings['x_moving'] or self.settings['y_moving']):
                self.update_timer.setInterval(10)
            else:
                self.update_timer.setInterval(1000)

    # Position reading methods
    def read_pos_x(self):
        """Read X position from hardware."""
        pos = self.stage.npos(self.x_axis)
        if pos is None:
            raise IOError(f"Failed to read X position (axis {self.x_axis})")
        return -pos if self.invert_x else pos

    def read_pos_y(self):
        """Read Y position from hardware."""
        pos = self.stage.npos(self.y_axis)
        if pos is None:
            raise IOError(f"Failed to read Y position (axis {self.y_axis})")
        return -pos if self.invert_y else pos

    # Movement status reading methods
    def read_x_moving(self):
        """Read X axis moving status from hardware using nstatus command."""
        moving = self.stage.is_moving(self.x_axis)
        if moving is None:
            raise IOError(f"Failed to read X moving status (axis {self.x_axis})")
        return moving

    def read_y_moving(self):
        """Read Y axis moving status from hardware using nstatus command."""
        moving = self.stage.is_moving(self.y_axis)
        if moving is None:
            raise IOError(f"Failed to read Y moving status (axis {self.y_axis})")
        return moving

    # Movement methods
    def move_x(self, target):
        """Move X axis to absolute position."""
        if self.invert_x:
            target = -target
        self.stage.nmove(target, self.x_axis)
        self.on_update_timer()

    def move_y(self, target):
        """Move Y axis to absolute position."""
        if self.invert_y:
            target = -target
        self.stage.nmove(target, self.y_axis)
        self.on_update_timer()

    def move_x_rel(self, distance):
        """Move X axis relative to current position."""
        if self.invert_x:
            distance = -distance
        self.stage.nrmove(distance, self.x_axis)

    def move_y_rel(self, distance):
        """Move Y axis relative to current position."""
        if self.invert_y:
            distance = -distance
        self.stage.nrmove(distance, self.y_axis)

    # Velocity settings
    def set_velocity_x(self, velocity):
        """Set X axis velocity."""
        self.stage.setnvel(velocity, self.x_axis)

    def set_velocity_y(self, velocity):
        """Set Y axis velocity."""
        self.stage.setnvel(velocity, self.y_axis)

    # Acceleration settings
    def set_acceleration_x(self, acceleration):
        """Set X axis acceleration."""
        self.stage.setnacc(acceleration, self.x_axis)

    def set_acceleration_y(self, acceleration):
        """Set Y axis acceleration."""
        self.stage.setnacc(acceleration, self.y_axis)

    # Deceleration settings
    def set_deceleration_x(self, deceleration):
        """Set X axis deceleration."""
        self.stage.setndec(deceleration, self.x_axis)

    def set_deceleration_y(self, deceleration):
        """Set Y axis deceleration."""
        self.stage.setndec(deceleration, self.y_axis)

    # Operation methods
    def halt_xy(self):
        """Emergency stop both axes."""
        self.stage.nstop(self.x_axis)
        self.stage.nstop(self.y_axis)

    def calibrate_x(self):
        """Calibrate (home) X axis."""
        self.stage.ncal(self.x_axis)

    def calibrate_y(self):
        """Calibrate (home) Y axis."""
        self.stage.ncal(self.y_axis)

    def calibrate_xy(self):
        """Calibrate (home) both X and Y axes."""
        self.stage.ncal(self.x_axis)
        self.stage.ncal(self.y_axis)

    # Status methods
    def is_busy_x(self):
        """Check if X axis is moving."""
        status = self.stage.is_moving(self.x_axis)
        return status

    def is_busy_y(self):
        """Check if Y axis is moving."""
        status = self.stage.is_moving(self.y_axis)
        return status

    def is_busy_xy(self):
        """Check if either axis is moving."""
        return self.is_busy_x() or self.is_busy_y()

    def wait_until_not_busy_xy(self, timeout=30.0):
        """Wait until both axes are not busy."""
        start_time = time.time()
        while self.is_busy_xy():
            time.sleep(0.05)
            if time.time() - start_time > timeout:
                raise TimeoutError("Stage movement timeout")
