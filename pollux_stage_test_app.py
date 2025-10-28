from ScopeFoundry import BaseMicroscopeApp
from micros_pollux_hw import MicrosPolluxStageHW
from pollux_stage_control_measure import PolluxStageControlMeasure


class PolluxStageTestApp(BaseMicroscopeApp):

    name = 'pollux_stage_test_app'

    def setup(self):
        # Add the Pollux stage hardware component
        hw = self.add_hardware(MicrosPolluxStageHW(
            self,
            x_axis=1,  # X axis number
            y_axis=2,  # Y axis number
            invert_x=False,
            invert_y=False
        ))

        # Configure serial port settings
        hw.settings['port'] = 'COM3'
        hw.settings['baudrate'] = 19260

        # Add the control measurement (UI)
        self.add_measurement(PolluxStageControlMeasure(self))


if __name__ == '__main__':
    import sys
    app = PolluxStageTestApp(sys.argv)
    app.exec_()
