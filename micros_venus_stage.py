import serial
import time
from typing import Optional, List, Tuple, Union
from enum import Enum
import threading 

class AxisState(Enum):
    """Axis state flags"""
    MOVING = "moving"
    READY = "ready"
    ERROR = "error"
    REFERENCED = "referenced"


class PolluxVenusStageController:
    """
    Complete Python interface for Pollux controller using Venus-2 protocol.
    Implements Venus-2 RPN (Reverse Polish Notation) command syntax.
    """
    
    def __init__(self, port: str, baudrate: int = 19260, timeout: float = 1.0, debug: bool=False):
        """
        Initialize connection to Pollux controller.
        
        Args:
            port: Serial port (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: Communication speed
            timeout: Read timeout in seconds
        """
        self.debug = debug
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        time.sleep(0.1)
        self._clear_buffer()
        self.lock = threading.Lock()
        
    def _clear_buffer(self):
        """Clear input buffer"""
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
    
    def send_command(self, command: str, wait_response: bool = True) -> str:
        """
        Send a Venus-2 command using RPN syntax.
        
        Args:
            command: Venus-2 command string (in RPN format)
            wait_response: Whether to wait for response
            
        Returns:
            Response from controller
        """
        if not command.endswith(' '):
            command += ' '
        
        if self.debug:
            t0 = time.monotonic()
            print(f"send_command: {repr(command)}")
        with self.lock:
            self.serial.write(command.encode('ascii'))
        
            if wait_response:
                response = self.serial.readline().decode('ascii').strip()
                if self.debug:
                    t1 = time.monotonic()
                    print(f"\t response: {repr(response)} [dt={t1-t0}]")
                return response
        return ""
    
    # ==========================================
    # MOVE COMMANDS (Blocking)
    # Venus-2 uses RPN: parameters first, then command
    # ==========================================
    
    def nmove(self, position: float, axis: int) -> str:
        """
        Move axis to absolute position.
        Blocking command - interpreter waits for completion.
        
        Venus-2 Syntax: [position] [axisno] nmove
        
        Args:
            position: Target position
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{position:1.6f} {axis} nmove", wait_response=False)
    
    def nrmove(self, distance: float, axis: int) -> str:
        """
        Move axis relative to current position.
        Blocking command.
        
        Venus-2 Syntax: [distance] [axisno] nrmove
        
        Args:
            distance: Relative distance to move
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{distance:1.6f} {axis} nrmove", wait_response=False)
    
    def ncal(self, axis: int) -> str:
        """
        Calibrate axis (move to reference position).
        Blocking command.
        
        Venus-2 Syntax: [axisno] ncal
        
        Args:
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{axis} ncal", wait_response=False)
    
    def nman(self, axis: int, direction: int = 1) -> str:
        """
        Start manual/continuous movement.
        
        Venus-2 Syntax: [axisno] nman+ or [axisno] nman- or [axisno] nman
        
        Args:
            axis: Axis number
            direction: 1 for positive, -1 for negative, 0 to stop
            
        Returns:
            Controller response
        """
        if direction > 0:
            cmd = f"{axis} nman+"
        elif direction < 0:
            cmd = f"{axis} nman-"
        else:
            cmd = f"{axis} nman"
        return self.send_command(cmd)
    
    def nstop(self, axis: int) -> str:
        """
        Stop axis movement.
        
        Venus-2 Syntax: [axisno] nstop
        
        Args:
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{axis} nstop")
    
    # ==========================================
    # PARAMETERIZATION COMMANDS
    # Venus-2 RPN: [value] [axisno] command
    # ==========================================
    
    def setnpos(self, position: float, axis: int) -> str:
        """
        Set current position value (blocking for safety).
        
        With the command setnpos the position origin of the axis
can be defined. The origin position is entered as a distance,
relative to the current axis location. If the origin is shifted, the
coordinates of the limits will be recalculated accordingly.

        Venus-2 Syntax: [position] [axisno] setnpos
        
        Args:
            position: New position value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{position} {axis} setnpos")
    
    def setaxisno(self, new_number: int, axis: int) -> str:
        """
        Change axis number (blocking).
        
        Venus-2 Syntax: [new_number] [axisno] setaxisno
        
        Args:
            new_number: New axis number
            axis: Current axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{new_number} {axis} setaxisno")
    
    def setcloop(self, enable: int, axis: int) -> str:
        """
        Enable/disable closed loop control (blocking).
        
        Venus-2 Syntax: [enable] [axisno] setcloop
        
        Args:
            enable: 1 to enable, 0 to disable
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{enable} {axis} setcloop")
    
    def setclperiod(self, period: int, axis: int) -> str:
        """
        Set closed loop period (blocking).
        
        Venus-2 Syntax: [period] [axisno] setclperiod
        
        Args:
            period: Period value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{period} {axis} setclperiod")
    
    def setpitch(self, pitch: float, axis: int) -> str:
        """
        Set pitch/lead of axis (blocking).
        
        Venus-2 Syntax: [pitch] [axisno] setpitch
        
        Args:
            pitch: Pitch value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{pitch} {axis} setpitch")
    
    def setpolepairs(self, pairs: int, axis: int) -> str:
        """
        Set number of pole pairs for motor (blocking).
        
        Venus-2 Syntax: [pairs] [axisno] setpolepairs
        
        Args:
            pairs: Number of pole pairs
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{pairs} {axis} setpolepairs")
    
    def setmotiondir(self, direction: int, axis: int) -> str:
        """
        Set motion direction (blocking).
        
        Venus-2 Syntax: [direction] [axisno] setmotiondir
        
        Args:
            direction: Direction value (1 or -1)
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{direction} {axis} setmotiondir")
    
    def setscaleinterface(self, interface: int, axis: int) -> str:
        """
        Set scale interface type (blocking).
        
        Venus-2 Syntax: [interface] [axisno] setscaleinterface
        
        Args:
            interface: Interface type code
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{interface} {axis} setscaleinterface")
    
    def setncode(self, code: int, axis: int) -> str:
        """
        Set encoder code (blocking).
        
        Venus-2 Syntax: [code] [axisno] setncode
        
        Args:
            code: Encoder code value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{code} {axis} setncode")
    
    def setaxis(self, enable: int, axis: int) -> str:
        """
        Enable/disable axis (blocking).
        
        Venus-2 Syntax: [enable] [axisno] setaxis
        
        Args:
            enable: 1 to enable, 0 to disable
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{enable} {axis} setaxis")
    
    def setphases(self, phases: int, axis: int) -> str:
        """
        Set motor phases (blocking).
        
        Venus-2 Syntax: [phases] [axisno] setphases
        
        Args:
            phases: Number of phases
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{phases} {axis} setphases")
    
    def setref(self, ref_type: int, axis: int) -> str:
        """
        Set reference type (blocking).
        
        Venus-2 Syntax: [ref_type] [axisno] setref
        
        Args:
            ref_type: Reference type code
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{ref_type} {axis} setref")
    
    def setblc(self, current: float, axis: int) -> str:
        """
        Set boost/limit current (blocking).
        
        Venus-2 Syntax: [current] [axisno] setblc
        
        Args:
            current: Current value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{current} {axis} setblc")
    
    def setblcd(self, delay: int, axis: int) -> str:
        """
        Set boost/limit current delay (blocking).
        
        Venus-2 Syntax: [delay] [axisno] setblcd
        
        Args:
            delay: Delay value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{delay} {axis} setblcd")
    
    def setblcs(self, standby: float, axis: int) -> str:
        """
        Set boost/limit current standby (blocking).
        
        Venus-2 Syntax: [standby] [axisno] setblcs
        
        Args:
            standby: Standby current value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{standby} {axis} setblcs")
    
    # Non-blocking parameterization commands
    
    def setnvel(self, velocity: float, axis: int) -> str:
        """
        Set velocity (non-blocking).
        
        Venus-2 Syntax: [velocity] [axisno] setnvel
        
        Args:
            velocity: Velocity value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{velocity} {axis} setnvel", wait_response=False)
    
    def setnacc(self, acceleration: float, axis: int) -> str:
        """
        Set acceleration (non-blocking).
        
        Venus-2 Syntax: [acceleration] [axisno] setnacc
        
        Args:
            acceleration: Acceleration value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{acceleration} {axis} setnacc", wait_response=False)
    
    def setndec(self, deceleration: float, axis: int) -> str:
        """
        Set deceleration (non-blocking).
        
        Venus-2 Syntax: [deceleration] [axisno] setndec
        
        Args:
            deceleration: Deceleration value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{deceleration} {axis} setndec", wait_response=False)
    
    def setnramp(self, ramp: float, axis: int) -> str:
        """
        Set ramp (non-blocking).
        
        Venus-2 Syntax: [ramp] [axisno] setnramp
        
        Args:
            ramp: Ramp value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{ramp} {axis} setnramp", wait_response=False)
    
    def setncalvel(self, velocity: float, axis: int) -> str:
        """
        Set calibration velocity (non-blocking).
        
        Venus-2 Syntax: [velocity] [axisno] setncalvel
        
        Args:
            velocity: Calibration velocity
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{velocity} {axis} setncalvel")
    
    def setnmanvel(self, velocity: float, axis: int) -> str:
        """
        Set manual movement velocity (non-blocking).
        
        Venus-2 Syntax: [velocity] [axisno] setnmanvel
        
        Args:
            velocity: Manual velocity
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{velocity} {axis} setnmanvel")
    
    def setnlimitmin(self, limit: float, axis: int) -> str:
        """
        Set minimum software limit (non-blocking).
        
        Venus-2 Syntax: [limit] [axisno] setnlimitmin
        
        Args:
            limit: Minimum limit value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{limit} {axis} setnlimitmin")
    
    def setnlimitmax(self, limit: float, axis: int) -> str:
        """
        Set maximum software limit (non-blocking).
        
        Venus-2 Syntax: [limit] [axisno] setnlimitmax
        
        Args:
            limit: Maximum limit value
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{limit} {axis} setnlimitmax")
    
    def setnlimitenable(self, enable: int, axis: int) -> str:
        """
        Enable/disable software limits (non-blocking).
        
        Venus-2 Syntax: [enable] [axisno] setnlimitenable
        
        Args:
            enable: 1 to enable, 0 to disable
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{enable} {axis} setnlimitenable")
    
    def setranddist(self, distance: float, axis: int) -> str:
        """
        Set random distance for nrandmove shake function.
        
        Venus-2 Syntax: [distance] [axisno] setranddist
        
        Args:
            distance: Distance for alternating positions (0 to disable)
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{distance} {axis} setranddist")
    
    # ==========================================
    # INQUIRY COMMANDS (Non-blocking except gne)
    # Venus-2 Syntax: [axisno] command
    # ==========================================
    
    def npos(self, axis: int) -> Optional[float]:
        """
        Get current position.
        
        Venus-2 Syntax: [axisno] npos
        
        Args:
            axis: Axis number
            
        Returns:
            Current position or None if error
        """
        response = self.send_command(f"{axis} npos")
        try:
            return float(response)
        except (ValueError, AttributeError):
            return None
    
    def nst(self, axis: int) -> str:
        """
        Get axis status.

        Venus-2 Syntax: [axisno] nst

        Args:
            axis: Axis number

        Returns:
            Status string
        """
        return self.send_command(f"{axis} nst")

    def nstatus(self, axis: int) -> Optional[int]:
        """
        Get current state of the axis as a decimal status code.

        The status code is a decimal value representing binary flags:
        D0 (1): Move in progress (0=finished, 1=in progress)
        D1 (2): no function
        D2 (4): Machine error occurred (Pollux NT only)
        D3 (8): no function
        D4 (16): Speed mode on/off
        D5 (32): Closed Loop In-Window function (Pollux NT only)
        D6 (64): Motor driver state (hardware option)
        D7 (128): Motion enable state (hardware option)

        Venus-2 Syntax: [axisno] nstatus

        Args:
            axis: Axis number

        Returns:
            Decimal status code or None if error
        """
        response = self.send_command(f"{axis} nstatus")
        try:
            return int(response)
        except (ValueError, AttributeError):
            return None

    def decode_nstatus(self, status_code: int) -> dict:
        """
        Decode the nstatus decimal value into individual status flags.

        Args:
            status_code: Decimal status code from nstatus command

        Returns:
            Dictionary with decoded status flags:
            - move_in_progress: bool (True=moving, False=finished)
            - machine_error: bool (Pollux NT only)
            - speed_mode: bool
            - closed_loop_in_window: bool (Pollux NT only)
            - motor_driver_enabled: bool (hardware option)
            - motion_enabled: bool (hardware option)
        """
        return {
            'move_in_progress': bool(status_code & 0b00000001),  # D0
            'machine_error': bool(status_code & 0b00000100),     # D2
            'speed_mode': bool(status_code & 0b00010000),        # D4
            'closed_loop_in_window': bool(status_code & 0b00100000),  # D5
            'motor_driver_enabled': bool(status_code & 0b01000000),   # D6
            'motion_enabled': bool(status_code & 0b10000000),    # D7
        }

    def is_moving(self, axis: int) -> Optional[bool]:
        """
        Check if axis is currently moving using nstatus command.

        Args:
            axis: Axis number

        Returns:
            True if moving, False if finished, None if error
        """
        status_code = self.nstatus(axis)
        if status_code is None:
            return None
        return bool(status_code & 0b00000001)
    
    def np(self) -> str:
        """
        Get all axes positions.
        
        Venus-2 Syntax: np
        
        Returns:
            Position string for all axes
        """
        return self.send_command("np")
    
    def gne(self) -> str:
        """
        Get number of errors (blocking).
        Blocks interpreter until current move is complete.
        
        Venus-2 Syntax: gne
        
        Returns:
            Number of errors
        """
        return self.send_command("gne")
    
    def nversion(self, axis: int) -> str:
        """
        Get axis firmware version.
        
        Venus-2 Syntax: [axisno] nversion
        
        Args:
            axis: Axis number
            
        Returns:
            Version string (space-separated numbers)
        """
        return self.send_command(f"{axis} nversion")
    
    def nidentify(self, axis: int) -> str:
        """
        Identify axis (related to nversion).
        
        Venus-2 Syntax: [axisno] nidentify
        
        Args:
            axis: Axis number
            
        Returns:
            Identification string
        """
        return self.send_command(f"{axis} nidentify")
    
    def getnvel(self, axis: int) -> Optional[float]:
        """
        Get velocity setting.
        
        Venus-2 Syntax: [axisno] getnvel
        
        Args:
            axis: Axis number
            
        Returns:
            Velocity value or None if error
        """
        response = self.send_command(f"{axis} getnvel")
        try:
            return float(response)
        except (ValueError, AttributeError):
            return None
    
    def getnacc(self, axis: int) -> Optional[float]:
        """
        Get acceleration setting.
        
        Venus-2 Syntax: [axisno] getnacc
        
        Args:
            axis: Axis number
            
        Returns:
            Acceleration value or None if error
        """
        response = self.send_command(f"{axis} getnacc")
        try:
            return float(response)
        except (ValueError, AttributeError):
            return None
    
    def getndec(self, axis: int) -> Optional[float]:
        """
        Get deceleration setting.
        
        Venus-2 Syntax: [axisno] getndec
        
        Args:
            axis: Axis number
            
        Returns:
            Deceleration value or None if error
        """
        response = self.send_command(f"{axis} getndec")
        try:
            return float(response)
        except (ValueError, AttributeError):
            return None
    
    def getnramp(self, axis: int) -> Optional[float]:
        """
        Get ramp setting.
        
        Venus-2 Syntax: [axisno] getnramp
        
        Args:
            axis: Axis number
            
        Returns:
            Ramp value or None if error
        """
        response = self.send_command(f"{axis} getnramp")
        try:
            return float(response)
        except (ValueError, AttributeError):
            return None
    
    def getncalvel(self, axis: int) -> Optional[float]:
        """
        Get calibration velocity.
        
        Venus-2 Syntax: [axisno] getncalvel
        
        Args:
            axis: Axis number
            
        Returns:
            Calibration velocity or None if error
        """
        response = self.send_command(f"{axis} getncalvel")
        try:
            return float(response)
        except (ValueError, AttributeError):
            return None
    
    def getnmanvel(self, axis: int) -> Optional[float]:
        """
        Get manual velocity.
        
        Venus-2 Syntax: [axisno] getnmanvel
        
        Args:
            axis: Axis number
            
        Returns:
            Manual velocity or None if error
        """
        response = self.send_command(f"{axis} getnmanvel")
        try:
            return float(response)
        except (ValueError, AttributeError):
            return None
    
    def getnlimitmin(self, axis: int) -> Optional[float]:
        """
        Get minimum software limit.
        
        Venus-2 Syntax: [axisno] getnlimitmin
        
        Args:
            axis: Axis number
            
        Returns:
            Minimum limit value or None if error
        """
        response = self.send_command(f"{axis} getnlimitmin")
        try:
            return float(response)
        except (ValueError, AttributeError):
            return None
    
    def getnlimitmax(self, axis: int) -> Optional[float]:
        """
        Get maximum software limit.
        
        Venus-2 Syntax: [axisno] getnlimitmax
        
        Args:
            axis: Axis number
            
        Returns:
            Maximum limit value or None if error
        """
        response = self.send_command(f"{axis} getnlimitmax")
        try:
            return float(response)
        except (ValueError, AttributeError):
            return None
    
    def getnlimitenable(self, axis: int) -> Optional[bool]:
        """
        Get software limit enable status.
        
        Venus-2 Syntax: [axisno] getnlimitenable
        
        Args:
            axis: Axis number
            
        Returns:
            True if enabled, False if disabled, None if error
        """
        response = self.send_command(f"{axis} getnlimitenable")
        try:
            return bool(int(response))
        except (ValueError, AttributeError):
            return None
    
    # ==========================================
    # STORAGE COMMANDS (Blocking)
    # ==========================================
    
    def nsave(self, axis: int) -> str:
        """
        Save axis parameters to non-volatile memory (blocking).
        
        Venus-2 Syntax: [axisno] nsave
        
        Args:
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{axis} nsave")
    
    def nrestore(self, axis: int) -> str:
        """
        Restore axis parameters from non-volatile memory (blocking).
        
        Venus-2 Syntax: [axisno] nrestore
        
        Args:
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{axis} nrestore")
    
    def getnfpara(self, axis: int) -> str:
        """
        Get factory parameters (blocking).
        
        Venus-2 Syntax: [axisno] getnfpara
        
        Args:
            axis: Axis number
            
        Returns:
            Factory parameters
        """
        return self.send_command(f"{axis} getnfpara")
    
    # ==========================================
    # SPECIAL COMMANDS
    # ==========================================
    
    def nrandmove(self, axis: int) -> str:
        """
        Execute random movement with randomized velocity.
        Use setranddist to enable "shake" function.
        
        Venus-2 Syntax: [axisno] nrandmove
        
        Args:
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{axis} nrandmove")
    
    def nabort(self, axis: int) -> str:
        """
        Abort current move on specific axis.
        
        Venus-2 Syntax: [axisno] nabort
        
        Args:
            axis: Axis number
            
        Returns:
            Controller response
        """
        return self.send_command(f"{axis} nabort")
    
    # ==========================================
    # EMERGENCY SHORTCUTS (Non-blocking)
    # ==========================================
    
    def emergency_stop(self) -> str:
        """
        Emergency stop (Ctrl-C equivalent).
        Terminates all axis movements.
        
        Returns:
            Controller response
        """
        return self.send_command("\x03", wait_response=False)  # Ctrl-C
    
    def abort_command(self) -> str:
        """
        Abort current command (Ctrl-B equivalent).
        
        Returns:
            Controller response
        """
        return self.send_command("\x02", wait_response=False)  # Ctrl-B
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    def wait_for_axis_ready(self, axis: int, timeout: float = 30.0, poll_interval: float = 0.1) -> bool:
        """
        Wait for axis to complete movement.
        
        Args:
            axis: Axis number
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks
            
        Returns:
            True if axis became ready, False if timeout
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            status = self.nst(axis)
            if 'ready' in status.lower() or not ('moving' in status.lower()):
                return True
            time.sleep(poll_interval)
        return False
    
    def move_and_wait(self, position: float, axis: int, timeout: float = 30.0) -> bool:
        """
        Move axis and wait for completion.
        
        Args:
            position: Target position
            axis: Axis number
            timeout: Maximum wait time
            
        Returns:
            True if move completed successfully
        """
        self.nmove(position, axis)
        return self.wait_for_axis_ready(axis, timeout)
    
    def calibrate_and_wait(self, axis: int, timeout: float = 60.0) -> bool:
        """
        Calibrate axis and wait for completion.
        
        Args:
            axis: Axis number
            timeout: Maximum wait time
            
        Returns:
            True if calibration completed successfully
        """
        self.ncal(axis)
        return self.wait_for_axis_ready(axis, timeout)
    
    def get_all_positions(self, axes: List[int]) -> dict:
        """
        Get positions for multiple axes.
        
        Args:
            axes: List of axis numbers
            
        Returns:
            Dictionary mapping axis number to position
        """
        positions = {}
        for axis in axes:
            pos = self.npos(axis)
            if pos is not None:
                positions[axis] = pos
        return positions
    
    def configure_axis(self, axis: int, velocity: float = None, 
                      acceleration: float = None, deceleration: float = None) -> None:
        """
        Configure multiple axis parameters at once.
        
        Args:
            axis: Axis number
            velocity: Velocity (optional)
            acceleration: Acceleration (optional)
            deceleration: Deceleration (optional)
        """
        if velocity is not None:
            self.setnvel(velocity, axis)
        if acceleration is not None:
            self.setnacc(acceleration, axis)
        if deceleration is not None:
            self.setndec(deceleration, axis)
    
    def close(self):
        """Close serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __del__(self):
        self.close()


# ==========================================
# EXAMPLE USAGE
# ==========================================

"""if __name__ == "__main__":
    # Basic usage example matching Venus-2 RPN syntax
    with VenusStageController(port='COM3', baudrate=9600) as stage:
        # Configure axis 1
        stage.setnvel(1000, 1)  # [velocity] [axis] setnvel
        stage.setnacc(500, 1)   # [acceleration] [axis] setnacc
        stage.setndec(500, 1)   # [deceleration] [axis] setndec
        
        # Calibrate axis 1
        print("Calibrating axis 1...")
        if stage.calibrate_and_wait(1):
            print("Calibration complete")
        
        # Move to position 5000
        print("Moving to position 5000...")
        stage.nmove(5000, 1)  # [position] [axis] nmove - correct RPN order!
        if stage.wait_for_axis_ready(1):
            print("Move complete")
        
        # Relative move
        stage.nrmove(0.5, 1)  # [distance] [axis] nrmove - correct RPN order!
        
        # Get current position
        pos = stage.npos(1)
        print(f"Current position: {pos}")
        
        # Get status
        status = stage.nst(1)
        print(f"Status: {status}")
        
        # Save parameters
        stage.nsave(1)
        print("Parameters saved")"""