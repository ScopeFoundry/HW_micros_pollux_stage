from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path


class PolluxStageControlMeasure(Measurement):

    name = 'Pollux_Stage_Control'

    def __init__(self, app, name=None, hw_name='micros_pollux_stage'):
        self.hw_name = hw_name
        Measurement.__init__(self, app, name=name)

    def setup(self):

        self.settings.New('jog_step_xy',
                         dtype=float, unit='mm',
                         initial=0.1, spinbox_decimals=4)

        self.stage = self.app.hardware[self.hw_name]

    def setup_figure(self):

        self.ui = load_qt_ui_file(sibling_path(__file__, 'pollux_stage_control.ui'))

        # Connect hardware connection checkbox
        self.stage.settings.connected.connect_to_widget(
            self.ui.pollux_stage_connect_checkBox)

        # Connect position displays (read-only)
        self.stage.settings.x_position.connect_to_widget(
            self.ui.x_pos_doubleSpinBox)
        self.stage.settings.y_position.connect_to_widget(
            self.ui.y_pos_doubleSpinBox)

        # Connect target position line edits
        self.ui.x_target_lineEdit.returnPressed.connect(
            self.stage.settings.x_target.update_value)
        self.ui.x_target_lineEdit.returnPressed.connect(
            lambda: self.ui.x_target_lineEdit.setText(""))
        self.ui.y_target_lineEdit.returnPressed.connect(
            self.stage.settings.y_target.update_value)
        self.ui.y_target_lineEdit.returnPressed.connect(
            lambda: self.ui.y_target_lineEdit.setText(""))

        # Connect jog step
        self.settings.jog_step_xy.connect_to_widget(
            self.ui.xy_step_doubleSpinBox)

        # Connect stop and calibration buttons
        self.ui.xy_stop_pushButton.clicked.connect(self.stage.halt_xy)
        self.ui.calibrate_xy_pushButton.clicked.connect(self.stage.calibrate_xy)

        # Connect velocity settings
        self.stage.settings.velocity_x.connect_to_widget(
            self.ui.velocity_x_doubleSpinBox)
        self.stage.settings.velocity_y.connect_to_widget(
            self.ui.velocity_y_doubleSpinBox)

        # Connect acceleration settings
        self.stage.settings.acceleration_x.connect_to_widget(
            self.ui.acceleration_x_doubleSpinBox)
        self.stage.settings.acceleration_y.connect_to_widget(
            self.ui.acceleration_y_doubleSpinBox)

        # Connect deceleration settings
        self.stage.settings.deceleration_x.connect_to_widget(
            self.ui.deceleration_x_doubleSpinBox)
        self.stage.settings.deceleration_y.connect_to_widget(
            self.ui.deceleration_y_doubleSpinBox)

        # Connect jog buttons
        self.ui.x_up_pushButton.clicked.connect(self.x_up)
        self.ui.x_down_pushButton.clicked.connect(self.x_down)
        self.ui.y_up_pushButton.clicked.connect(self.y_up)
        self.ui.y_down_pushButton.clicked.connect(self.y_down)

    def x_up(self):
        self.stage.settings['x_target'] += self.settings['jog_step_xy']

    def x_down(self):
        self.stage.settings['x_target'] -= self.settings['jog_step_xy']

    def y_up(self):
        self.stage.settings['y_target'] += self.settings['jog_step_xy']

    def y_down(self):
        self.stage.settings['y_target'] -= self.settings['jog_step_xy']
