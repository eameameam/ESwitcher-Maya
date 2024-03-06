# ESwitcher: Maya Attribute and Snap Switcher

The `ESwitcher` script offers an intuitive interface for managing multiple control attributes in Autodesk Maya. It enhances the workflow for animators and riggers by providing a centralized tool to switch between global and local attributes, snap to world or object coordinates, and directly lock controller attributes to corresponding bone attributes. The script also includes a memory feature that stores rig parameters temporarily in Maya's memory, allowing for quick recall.

![ESwitcher Window](/ESwitcher.png)

## Installation

1. Place the `ESwitcher.py` file in the `scripts` folder of your Maya directory.
2. Assign a hotkey in Maya's Hotkey Editor:
```python
import ESwitcher
ESwitcher.create_popup()
```

## Usage

To access ESwitcher, simply press the assigned hotkey.

The ESwitcher interface will appear, providing options to:

1. Switch Global/Follow Attribute in a range or a single frame.
2. Snap controls to world coordinates or to another object.
3. Lock a control, such as a knee controller, to its corresponding bone and switch Lock Attribute.
