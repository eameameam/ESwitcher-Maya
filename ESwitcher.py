import math
import os

import maya.OpenMayaUI as omui
import maya.cmds as cmds
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt, QPointF, QLineF, QTimer
from PySide2.QtGui import QColor, QCursor, QPainter, QPen, QMouseEvent
from PySide2.QtWidgets import QApplication
from shiboken2 import wrapInstance
import maya.OpenMaya as OpenMaya
import re

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

windows = {
    'left': None,
    'right': None,
    'bottom': None,
    'middle': None,
    'topleft' : None,
    'topright' : None,
    'middletopleft' : None,
    'middletopright' : None,
    'settingssmall' : None
}

class CircleWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CircleWidget, self).__init__(parent)
        self.line_to_cursor = None
        self.setMouseTracking(True)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_line_to_cursor)
        self.timer.start(10)

    def update_line_to_cursor(self):
        widget_center = self.rect().center()
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        dx = cursor_pos.x() - widget_center.x()
        dy = cursor_pos.y() - widget_center.y()
        angle = math.atan2(dy, dx)
        line_length = math.sqrt(dx**2 + dy**2)

        cursor_over_window = False
        for window in windows.values():
            if window and window.underMouse():
                cursor_over_window = True
                break

        if line_length > 200 or cursor_over_window:
            self.line_to_cursor = None
        else:
            new_x = widget_center.x() + line_length * math.cos(angle)
            new_y = widget_center.y() + line_length * math.sin(angle)
            new_end_point = QPointF(new_x, new_y)
            line = QLineF(widget_center, new_end_point)
            self.line_to_cursor = line
        self.update()

    def paintEvent(self, event):
        if self.line_to_cursor is not None:
            painter = QPainter(self)
            color = QColor(20, 20, 20, 150)
            pen = QPen(color, 4)
            painter.setRenderHint(QPainter.Antialiasing, True) 
            painter.setPen(pen)
            painter.drawLine(self.line_to_cursor)

    def closeEvent(self, event):
        self.timer.stop()

class MiddlePoint(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(MiddlePoint, self).__init__(parent)

        self.setFixedSize(400, 400)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool | QtCore.Qt.WindowTransparentForInput)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        self.installEventFilter(self)

        self.frame = CircleWidget(self)
        self.frame.setGeometry(0, 0, self.width(), self.height())

        self.center_widget = QtWidgets.QWidget(self)
        self.center_widget.setGeometry(self.width()//2 - 5, self.height()//2 - 5, 10, 10)
        self.center_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 240);
                border-radius: 5px;
            }""")

        self.setMouseTracking(True)
        self.show()

class BasePopupWindow(QtWidgets.QDialog):
    attribute_to_optionvar = {
        'Follow': 'ESwitch_Follow',
        'Global': 'ESwitch_Global',
        'GlobalTranslate': 'ESwitch_GlobalTranslate',
        'Lock': 'ESwitch_Lock',
    }



    def __init__(self, parent=maya_main_window(), icon_name="", attribute_name=""):
        super(BasePopupWindow, self).__init__(parent)     
        
        self.setFixedSize(70, 40)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        self.setWindowOpacity(0.9)
        self.installEventFilter(self)

        icon_folder = os.path.join(cmds.internalVar(userPrefDir=True), "icons", "ESwitch")

        self.frame = QtWidgets.QWidget(self)


        self.main_layout = QtWidgets.QVBoxLayout(self.frame)
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        label = QtWidgets.QLabel(self.frame)
        pixmap = QtGui.QPixmap(os.path.join(icon_folder, "{}.png".format(icon_name)))
        label.setPixmap(pixmap)
        label.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(label)

        self.show()
        
        self.attribute_name = attribute_name

    def enterEvent(self, event):
        print(self.attribute_name)
        try:
            for window_name in ['left', 'bottom', 'right', 'middle', 'topleft', 'topright', 'middletopleft', 'middletopright', 'settingssmall']:
                if windows[window_name] is not None:
                    windows[window_name].close()
                    windows[window_name] = None
        except:
            pass
        
        optionvar_key = self.attribute_to_optionvar.get(self.attribute_name, self.attribute_name)
        
        attribute_name = cmds.optionVar(q=optionvar_key) or self.attribute_name
        
        attribute_instance = AttributeSwitch(attribute_name)
        
        event.accept()   

class GlobalPopupWindow(BasePopupWindow):
    def __init__(self, parent=maya_main_window()):
        super(GlobalPopupWindow, self).__init__(parent, icon_name="Global", attribute_name="Global")
        
        self.frame.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 10px;
                max-width: 70;
                min-height: 40;
            }
        """)

class GlobalTranslatePopupWindow(BasePopupWindow):
    def __init__(self, parent=maya_main_window()):
        super(GlobalTranslatePopupWindow, self).__init__(parent, icon_name="GlobalTranslate", attribute_name="GlobalTranslate")

        self.frame.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 10px;
                max-width: 70;
                min-height: 40;
            }
        """)

class FollowPopupWindow(BasePopupWindow):
    def __init__(self, parent=maya_main_window()):
        super(FollowPopupWindow, self).__init__(parent, icon_name="Follow", attribute_name="Follow")

        self.frame.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 10px;
                max-width: 70;
                min-height: 40;
            }
        """)

class WorldSnapPopupWindow(BasePopupWindow):
    def __init__(self, parent=maya_main_window()):
        super(WorldSnapPopupWindow, self).__init__(parent, icon_name="WorldSnap")

        self.frame.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 10px;
                max-width: 70;
                min-height: 40;
            }
        """)
        
class SettingsSmallPopupWindow(BasePopupWindow):
    def __init__(self, parent=maya_main_window()):
        super(SettingsSmallPopupWindow, self).__init__(parent, icon_name="SettingsSmall")

        self.position = None    
        self.frame.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 20px;
                max-width: 40;
                min-height: 40;
            }
        """)
        self.setFixedSize(40, 40)
        
        self.settings_window = None
            

    def enterEvent(self, event):
        if not any(windows[key] and key != 'bottom' for key in windows):
            return

        self.close()
        cursor_position = self.mapToGlobal(QtCore.QPoint(0, 0))
        position_offset = QtCore.QPoint(-80, 0)
        self.settings_window = SettingsPopupWindow(self, position=cursor_position + position_offset)
        self.settings_window.show()

    def show_settings_window(self):
        self.settings_window = SettingsPopupWindow(self, position=self.position)
        self.settings_window.show()


class ObjSnapPopupWindow(BasePopupWindow):
    def __init__(self, parent=maya_main_window()):
        super(ObjSnapPopupWindow, self).__init__(parent, icon_name="ObjectSnap")

        self.frame.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 10px;
                max-width: 70;
                min-height: 40;
            }
        """)

    def enterEvent(self, event):
        try:
            for window_name in ['left', 'bottom', 'right', 'middle', 'topleft', 'topright', 'middletopleft', 'middletopright', 'settingssmall']:
                if windows[window_name] is not None:
                    windows[window_name].close()
                    windows[window_name] = None
        except:
            pass

        attribute_instance = ObjSnap()

        event.accept()

class LockPopupWindow(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(LockPopupWindow, self).__init__(parent)
        
        self.setFixedSize(70, 40)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        self.setWindowOpacity(0.9)
        self.installEventFilter(self)

        icon_folder = os.path.join(cmds.internalVar(userPrefDir=True), "icons", "ESwitch")

        self.frame = QtWidgets.QWidget(self)
        self.frame.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 10px;
                max-width: 70;
                min-height: 40;
            }
        """)

        self.main_layout = QtWidgets.QVBoxLayout(self.frame)
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        label = QtWidgets.QLabel(self.frame)
        pixmap = QtGui.QPixmap(os.path.join(icon_folder, "Lock.png"))
        label.setPixmap(pixmap)
        label.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(label)

        self.show()

    def enterEvent(self, event):
        if isinstance(self, LockPopupWindow):        
            print("Lock")
            try:
                for window_name in ['left', 'bottom', 'right', 'middle', 'topleft', 'topright', 'middletopleft', 'middletopright', 'settingssmall']:
                    if windows[window_name] is not None:
                        windows[window_name].close()
                        windows[window_name] = None
            except:
                pass
            
            lock_attr_name = cmds.optionVar(q="ESwitch_Lock") or 'Lock'
            lock_instance = Lock(lock_attr_name)
        event.accept()



class SettingsPopupWindow(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window(), position=None):
        super(SettingsPopupWindow, self).__init__(parent)
        self.close_in_progress = False 
        
        self.setFixedSize(210, 300)

        if position is not None:
            self.move(position)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        self.setWindowOpacity(0.9)
        self.installEventFilter(self)

        icon_folder = os.path.join(cmds.internalVar(userPrefDir=True), "icons", "ESwitch")

        self.frame = QtWidgets.QWidget(self)
        self.frame.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 10px;
                min-width: 210;
                min-height: 300;                
            }
        """)

        self.main_layout = QtWidgets.QVBoxLayout(self.frame)
        self.setLayout(self.main_layout)
        
        self.title_logo_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.title_logo_layout)

        self.about_layout = QtWidgets.QVBoxLayout()
        self.about_layout.setAlignment(QtCore.Qt.AlignTop)   
        self.title_logo_layout.addLayout(self.about_layout)

        self.about_button = QtWidgets.QPushButton()
        icon_folder = os.path.join(cmds.internalVar(userPrefDir=True), "icons", "ESwitch")
        self.about_button.setIcon(QtGui.QIcon(os.path.join(icon_folder, "E.png")))
        self.about_button.setIconSize(QtCore.QSize(20, 20))
        self.about_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 10px;
                min-width: 0;
                min-height: 0;
            }
            QPushButton::hover {
                background-color: rgba(40, 40, 40, 240);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 240);
            }
            QPushButton[active="true"] {
                background-color: rgba(82, 133, 166, 240);
            }
        """)
        self.about_button.setFixedSize(20, 20)
        self.about_button.clicked.connect(self.about)
        self.about_layout.addWidget(self.about_button)

        self.logo_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(os.path.join(icon_folder, "ESwitch.png"))
        pixmap = pixmap.scaled(100, 70, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)  # Resize pixmap
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setStyleSheet("border: none;")
        self.title_logo_layout.addStretch()
        self.title_logo_layout.addWidget(self.logo_label)     
        self.title_logo_layout.addStretch()   

        self.close_layout = QtWidgets.QVBoxLayout()
        self.close_layout.setAlignment(QtCore.Qt.AlignTop)
        self.title_logo_layout.addLayout(self.close_layout)

        self.close_button = QtWidgets.QPushButton()
        self.close_button.setIcon(QtGui.QIcon(os.path.join(icon_folder, "closeButton.png")))
        self.close_button.setIconSize(QtCore.QSize(20, 20))
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(10, 10, 10, 240);
                border-radius: 10px;
                min-width: 0;
                min-height: 0;
            }
            QPushButton::hover {
                background-color: rgba(40, 40, 40, 240);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 240);
            }
            QPushButton[active="true"] {
                background-color: rgba(82, 133, 166, 240);
            }
        """)
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.close_all_windows)
        self.close_layout.addWidget(self.close_button)

        self.follow_attribute_label = QtWidgets.QLabel("The Follow attr name:", self)
        self.follow_attribute_label.setStyleSheet("font-size: 13px;")      
        self.follow_attribute_field = QtWidgets.QLineEdit(self)
        self.follow_attribute_field.setFixedHeight(20)
        self.follow_attribute_field.setStyleSheet("font-size: 13px;") 

        self.global_attribute_label = QtWidgets.QLabel("The Global attr name:", self)
        self.global_attribute_label.setStyleSheet("font-size: 13px;")  
        self.global_attribute_field = QtWidgets.QLineEdit(self)
        self.global_attribute_field.setFixedHeight(20)
        self.global_attribute_field.setStyleSheet("font-size: 13px;")

        self.globalTranslate_attribute_label = QtWidgets.QLabel("The GlobalTranslate attr name:", self)
        self.globalTranslate_attribute_label.setStyleSheet("font-size: 13px;")  
        self.globalTranslate_attribute_field = QtWidgets.QLineEdit(self)
        self.globalTranslate_attribute_field.setFixedHeight(20)
        self.globalTranslate_attribute_field.setStyleSheet("font-size: 13px;")

        self.lock_attribute_label = QtWidgets.QLabel("The Lock attr name:", self)
        self.lock_attribute_label.setStyleSheet("font-size: 13px;")  
        self.lock_attribute_field = QtWidgets.QLineEdit(self)
        self.lock_attribute_field.setFixedHeight(20)
        self.lock_attribute_field.setStyleSheet("font-size: 13px;")   

        self.elbow_name_label = QtWidgets.QLabel("The Bones names:", self)
        self.elbow_name_label.setStyleSheet("font-size: 13px;") 

        self.bone_names_layout = QtWidgets.QHBoxLayout()

        self.elbow_name_field = QtWidgets.QLineEdit(self)
        self.elbow_name_field.setFixedHeight(20)
        self.elbow_name_field.setStyleSheet("font-size: 13px;")   
        self.knee_name_field = QtWidgets.QLineEdit(self)
        self.knee_name_field.setFixedHeight(20)
        self.knee_name_field.setStyleSheet("font-size: 13px;")  
        self.bone_names_layout.addWidget(self.elbow_name_field)         
        self.bone_names_layout.addWidget(self.knee_name_field)     

        self.main_layout.addWidget(self.follow_attribute_label)
        self.main_layout.addWidget(self.follow_attribute_field)
        self.main_layout.addWidget(self.global_attribute_label)
        self.main_layout.addWidget(self.global_attribute_field)
        self.main_layout.addWidget(self.globalTranslate_attribute_label)
        self.main_layout.addWidget(self.globalTranslate_attribute_field)        
        self.main_layout.addWidget(self.lock_attribute_label)
        self.main_layout.addWidget(self.lock_attribute_field)      
        self.main_layout.addWidget(self.elbow_name_label)
        self.main_layout.addLayout(self.bone_names_layout)    
        
        follow_attribute_value = cmds.optionVar(q="ESwitch_Follow")
        global_attribute_value = cmds.optionVar(q="ESwitch_Global")
        globalTranslate_attribute_value = cmds.optionVar(q="ESwitch_GlobalTranslate")
        lock_attribute_value = cmds.optionVar(q="ESwitch_Lock")
        elbow_name_value = cmds.optionVar(q="ESwitch_Elbow")        
        knee_name_value = cmds.optionVar(q="ESwitch_Knee")            
        self.follow_attribute_field.setText(follow_attribute_value or 'Follow')
        self.global_attribute_field.setText(global_attribute_value or 'Global')
        self.globalTranslate_attribute_field.setText(globalTranslate_attribute_value or 'GlobalTranslate')
        self.lock_attribute_field.setText(lock_attribute_value or 'Lock')
        self.elbow_name_field.setText(elbow_name_value or 'Elbow')
        self.knee_name_field.setText(knee_name_value or 'Knee')

        self.show()
        
    def enterEvent(self, event):
        pass

    def leaveEvent(self, event):
        if self.isVisible() and not self.close_in_progress:
            self.close_and_show_small_popup_window()
        event.ignore()

    def close_and_show_small_popup_window(self):
        self.close_in_progress = True
        self.close()
        self.parent().show()
        self.close_in_progress = False

    def about(self):
        if not self.close_in_progress:
            self.close_in_progress = True
            self.close()
            self.about_dialog = AboutDialog(self)
            self.about_dialog.show()
            self.close_in_progress = False

    def close_all_windows(self):
        if not self.close_in_progress:
            if isinstance(self, SettingsPopupWindow):
                self.close()
                try:
                    for window_name in ['left', 'bottom', 'right', 'middle', 'topleft', 'topright', 'middletopleft', 'middletopright', 'settingssmall']:
                        if windows[window_name] is not None:
                            windows[window_name].close()
                            windows[window_name] = None
                except:
                    pass



     
    def closeEvent(self, event):
        if not isinstance(self, SettingsSmallPopupWindow):
            cmds.optionVar(sv=("ESwitch_Follow", self.follow_attribute_field.text()))
            cmds.optionVar(sv=("ESwitch_Global", self.global_attribute_field.text()))
            cmds.optionVar(sv=("ESwitch_GlobalTranslate", self.globalTranslate_attribute_field.text()))        
            cmds.optionVar(sv=("ESwitch_Lock", self.lock_attribute_field.text()))        
            cmds.optionVar(sv=("ESwitch_Elbow", self.elbow_name_field.text()))                
            cmds.optionVar(sv=("ESwitch_Knee", self.knee_name_field.text()))   

        super(SettingsPopupWindow, self).closeEvent(event)

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool | QtCore.Qt.Popup)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setFixedSize(250, 250)
        layout = QtWidgets.QVBoxLayout(self)
        logo_label = QtWidgets.QLabel()
        icon_folder = os.path.join(cmds.internalVar(userPrefDir=True), "icons", "ESwitch")
        movie = QtGui.QMovie(os.path.join(icon_folder, "about.gif"))
        movie.setCacheMode(QtGui.QMovie.CacheAll)
        movie.setScaledSize(QtCore.QSize(200, 200))
        movie.frameChanged.connect(self.movie_frame_changed) 
        logo_label.setMovie(movie)
        logo_label.setStyleSheet("border: none;")
        layout.addWidget(logo_label)
        self.setLayout(layout)
        movie.start() 

    def showEvent(self, event):
        button_geo = self.parent().about_button.geometry()
        x = button_geo.x() + button_geo.width() / 2 - self.width() / 2 + 15
        y = button_geo.y() + button_geo.height() / 2 - self.height() / 2
        self.move(self.parent().mapToGlobal(QtCore.QPoint(x, y)))

    def leaveEvent(self, event):
        self.close()

    def movie_frame_changed(self, frame_number):
        movie = self.sender()
        if frame_number == movie.frameCount() - 1:
            movie.setPaused(True)

class AttributeSwitch:
    def __init__(self, attr_name):
        self.attr_name = attr_name
        
        self.selected_objects = cmds.ls(selection=True)

        self.time_slider_selection = cmds.timeControl("timeControl1", q=True, rangeArray=True)

        self.current_selection = cmds.ls(selection=True)

        self.current_tool = cmds.currentCtx()

        cmds.undoInfo(openChunk=True)

        cmds.setToolTo('moveSuperContext')

        if not self.selected_objects:
            cmds.inViewMessage(amg="No objects selected. Please select objects.", pos="topCenter", fade=True)
        else:
            for obj in self.selected_objects:
                self.process_object(obj)

        cmds.setToolTo(self.current_tool)
        
        if self.current_selection:
            cmds.select(self.current_selection)

        cmds.undoInfo(closeChunk=True)

    def process_object(self, obj):
        attrs = cmds.listAttr(obj)

        if not attrs:
            return 
        
        if self.attr_name not in attrs:
            cmds.inViewMessage(amg="No '{}' attribute found for {}. Locator not created.".format(self.attr_name, obj), pos="topCenter", fade=True)
            return

        attr_name_orig = self.attr_name

        if self.time_slider_selection:
            keyframes = cmds.keyframe(obj, attribute=attr_name_orig, query=True, time=(self.time_slider_selection[0], self.time_slider_selection[1]))
            if keyframes:
                for keyframe in keyframes:
                    cmds.currentTime(keyframe)
                    self.process_keyframe(obj, attr_name_orig, keyframes=True)
            else:
                self.process_keyframe(obj, attr_name_orig, keyframes=False)

    def process_keyframe(self, obj, attr_name, keyframes=False):
        loc = cmds.spaceLocator(name="Locator#{}".format(obj))

        cmds.matchTransform(loc[0], obj, pos=True, rot=True, scl=True)

        attr_value = cmds.getAttr("{}.{}".format(obj, attr_name))
        attr_min_value = cmds.addAttr("{}.{}".format(obj, attr_name), q=True, min=True)
        attr_max_value = cmds.addAttr("{}.{}".format(obj, attr_name), q=True, max=True)
        mid_point = attr_min_value + ((attr_max_value - attr_min_value) / 2)

        if attr_value >= mid_point:
            cmds.setAttr("{}.{}".format(obj, attr_name), attr_min_value)
        else:
            cmds.setAttr("{}.{}".format(obj, attr_name), attr_max_value)

        if keyframes or cmds.keyframe(obj, attribute=attr_name, query=True):
            cmds.setKeyframe(obj, attribute=attr_name)

        cmds.matchTransform(obj, loc[0], pos=True, rot=True, scl=True)

        cmds.delete(loc[0])

        cmds.inViewMessage(amg="'{}' attribute switched for {}.".format(attr_name, obj), pos="topCenter", fade=True)

class Lock:
    def __init__(self, lock_attr_name):
        self.selected_objects = cmds.ls(selection=True)

        cmds.undoInfo(openChunk=True)

        if not self.selected_objects:
            cmds.inViewMessage(amg="No objects selected. Please select objects.", pos="topCenter", fade=True)
            return

        self.current_selection = cmds.ls(selection=True)

        self.current_tool = cmds.currentCtx()
        cmds.setToolTo('moveSuperContext')

        self.time_slider_selection = cmds.timeControl("timeControl1", q=True, rangeArray=True)

        for controller in self.selected_objects:
            self.process_controller(controller, lock_attr_name)

        cmds.setToolTo(self.current_tool)

        if self.current_selection:
            cmds.select(self.current_selection)

        cmds.undoInfo(closeChunk=True)

    def process_controller(self, controller, lock_attr_name):
        attrs = [attr.lower() for attr in cmds.listAttr(controller)]
        
        if lock_attr_name.lower() in attrs:
            lock_attr_name_orig = cmds.listAttr(controller)[attrs.index(lock_attr_name.lower())]

            joint = self.identify_joint(controller)

            if joint:
                if self.time_slider_selection:
                    keyframes = cmds.keyframe(controller, attribute=lock_attr_name_orig, query=True, time=(self.time_slider_selection[0], self.time_slider_selection[1]))
                    if keyframes:
                        for keyframe in keyframes:
                            cmds.currentTime(keyframe)
                            self.process_keyframe(controller, joint, lock_attr_name_orig, keyframes=True)
                    else:
                        self.process_keyframe(controller, joint, lock_attr_name_orig, keyframes=False)
                else:
                    self.process_keyframe(controller, joint, lock_attr_name_orig, keyframes=False)
            else:
                cmds.inViewMessage(amg="No joint identified for {}. Locator not created.".format(controller), pos="topCenter", fade=True)

        else:
            cmds.inViewMessage(amg="No '{}' attribute found for {}. Locator not created.".format(lock_attr_name, controller), pos="topCenter", fade=True)


        cmds.setToolTo(self.current_tool)

        if self.current_selection:
            cmds.select(self.current_selection)

    def process_keyframe(self, controller, joint, lock_attr_name, keyframes=False):
        loc = cmds.spaceLocator(name="Locator#{}".format(controller))
        cmds.matchTransform(loc[0], joint, pos=True, rot=True, scl=True)

        lock_value = cmds.getAttr("{}.{}".format(controller, lock_attr_name))
        lock_min_value = cmds.addAttr("{}.{}".format(controller, lock_attr_name), q=True, min=True)
        lock_max_value = cmds.addAttr("{}.{}".format(controller, lock_attr_name), q=True, max=True)
        mid_point = lock_min_value + ((lock_max_value - lock_min_value) / 2)

        if lock_value >= mid_point:
            cmds.setAttr("{}.{}".format(controller, lock_attr_name), lock_min_value)
        else:
            cmds.setAttr("{}.{}".format(controller, lock_attr_name), lock_max_value)

        if keyframes or cmds.keyframe(controller, attribute=lock_attr_name, query=True):
            cmds.setKeyframe(controller, attribute=lock_attr_name)

        cmds.matchTransform(controller, loc[0], pos=True, rot=True, scl=True)

        cmds.delete(loc[0])

        cmds.inViewMessage(amg="'{}' attribute switched for {}.".format(lock_attr_name, controller), pos="topCenter", fade=True)

    def identify_joint(self, controller):
        controller_suffix = self.get_suffix(controller)

        elbow_name = cmds.optionVar(q="ESwitch_Elbow")
        knee_name = cmds.optionVar(q="ESwitch_Knee")

        return self.recursive_search(controller, controller_suffix, [elbow_name, knee_name], [])


    @staticmethod
    def get_suffix(name):
        match = re.search(r'[lr]$', name, re.IGNORECASE)
        if match:
            return match.group(0)
        else:
            return None

    def recursive_search(self, node, suffix, joint_names, checked_nodes):
        connected_nodes = [n for n in cmds.listConnections(node) or [] if n not in checked_nodes]

        for node in connected_nodes:
            if isinstance(node, str) and suffix.lower() in node.lower() and any(joint_name in node for joint_name in joint_names):
                return node
            else:
                checked_nodes.append(node)
                result = self.recursive_search(node, suffix, joint_names, checked_nodes)
                if result:
                    return result

        return None

class WorldSnap:
    def __init__(self):
        self.selected_objects = cmds.ls(selection=True)
        self.time_slider_selection = cmds.timeControl("timeControl1", q=True, rangeArray=True)
        self.current_selection = cmds.ls(selection=True)
        self.current_tool = cmds.currentCtx()

        cmds.undoInfo(openChunk=True)

        cmds.setToolTo('moveSuperContext')

        if not self.validate():
            cmds.setToolTo(self.current_tool)
            return

        for obj in self.selected_objects:
            self.process_object(obj)

        cmds.setToolTo(self.current_tool)
        if self.current_selection:
            cmds.select(self.current_selection)

        cmds.undoInfo(closeChunk=True)

    def validate(self):
        if not self.selected_objects:
            cmds.inViewMessage(amg="No objects selected. Please select objects.", pos="topCenter", fade=True)
            return False
        elif not self.time_slider_selection:
            cmds.inViewMessage(amg="No time range selected. Please select a time range.", pos="topCenter", fade=True)
            return False
        return True

    def process_object(self, obj):
        loc = cmds.spaceLocator(name="Locator#{}".format(obj))
        cmds.matchTransform(loc[0], obj, pos=True, rot=True, scl=True)
        keyframes = range(int(self.time_slider_selection[0]), int(self.time_slider_selection[1]) + 1)
        
        if keyframes:
            for keyframe in keyframes:
                cmds.currentTime(keyframe)
                self.process_keyframe(obj, loc[0])
                
        cmds.delete(loc[0])

    def process_keyframe(self, obj, loc):
        cmds.matchTransform(obj, loc, pos=True, rot=True, scl=True)
        cmds.setKeyframe(obj)
        cmds.inViewMessage(amg="World Snap processed for {}.".format(obj), pos="topCenter", fade=True)

class ObjSnap:
    def __init__(self):
        self.selected_objects = cmds.ls(selection=True)
        self.time_slider_selection = cmds.timeControl("timeControl1", q=True, rangeArray=True)
        self.current_selection = cmds.ls(selection=True)
        self.current_tool = cmds.currentCtx()

        cmds.undoInfo(openChunk=True)

        cmds.setToolTo('moveSuperContext')

        if not self.validate():
            cmds.setToolTo(self.current_tool)
            return

        self.target_object, self.control_object = self.selected_objects
        self.process_object()

        cmds.setToolTo(self.current_tool)
        if self.current_selection:
            cmds.select(self.current_selection)

        # Close the undo chunk
        cmds.undoInfo(closeChunk=True)

    def validate(self):
        if not self.selected_objects or len(self.selected_objects) != 2:
            cmds.inViewMessage(amg="Please select two objects. The first one should be the target, and the second one should be the child.", pos="topCenter", fade=True)
            return False
        elif not self.time_slider_selection:
            cmds.inViewMessage(amg="No time range selected. Please select a time range.", pos="topCenter", fade=True)
            return False
        return True

    def process_object(self):
        loc = cmds.spaceLocator(name="Locator#{}".format(self.target_object))
        cmds.pointConstraint(self.target_object, loc, maintainOffset=False)
        
        control_parent = cmds.listRelatives(self.control_object, parent=True)[0]
        constraint = cmds.pointConstraint(loc, control_parent, maintainOffset=True)
        
        keyframes = range(int(self.time_slider_selection[0]), int(self.time_slider_selection[1]) + 1)
        if keyframes:
            for keyframe in keyframes:
                cmds.currentTime(keyframe)
                cmds.setKeyframe(control_parent, attribute='translate')
        
        cmds.delete(constraint)
        cmds.delete(loc)

        cmds.inViewMessage(amg="Object Snap processed for {}.".format(self.control_object), pos="topCenter", fade=True)


initial_cursor_position = QtGui.QCursor().pos()

def create_popup_window(window_class, position_offset, name, cursor_position=None):
    if cursor_position is None:
        cursor_position = initial_cursor_position
    window = window_class()
    window.move(cursor_position - window.rect().center() + position_offset)
    windows[name] = window 
    return window

def create_popup():
    cursor_position = QtGui.QCursor().pos()

    left_window = create_popup_window(GlobalTranslatePopupWindow, QtCore.QPoint(-100, 50), 'left', cursor_position)
    topleft_window = create_popup_window(GlobalPopupWindow, QtCore.QPoint(-150, -10), 'topleft', cursor_position)
    topright_window = create_popup_window(LockPopupWindow, QtCore.QPoint(150, -10), 'topright', cursor_position)
    right_window = create_popup_window(FollowPopupWindow, QtCore.QPoint(100, 50), 'right', cursor_position)
    middle_top_right_window = create_popup_window(WorldSnapPopupWindow, QtCore.QPoint(-70, -70), 'middletopright', cursor_position)
    middle_top_left_window = create_popup_window(ObjSnapPopupWindow, QtCore.QPoint(70, -70), 'middletopleft', cursor_position)

    middle_window = create_popup_window(MiddlePoint, QtCore.QPoint(0, 0), 'middle', cursor_position)
    bottom_small_window = create_popup_window(SettingsSmallPopupWindow, QtCore.QPoint(0, 100), 'settingssmall', cursor_position)

def close_popup():
    global windows
    for window in windows.values():
        if window is not None:
            window.close()

