import os
import streamlit.components.v1 as components

# Đường dẫn tới folder webcam_component
_COMPONENT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "webcam_component"
)

print(f"🔥 Component path: {_COMPONENT_PATH}")
print(f"🔥 Path exists: {os.path.exists(_COMPONENT_PATH)}")
print(f"🔥 index.html exists: {os.path.exists(os.path.join(_COMPONENT_PATH, 'index.html'))}")

# Khai báo component
_webcam_component = components.declare_component(
    "webcam_component",
    path=_COMPONENT_PATH
)

def capture_component(start_capture=False, key=None):
    """
    Webcam component để chụp 25 ảnh tự động
    """
    component_value = _webcam_component(
        start_capture=start_capture,
        default=None,
        key=key
    )
    
    print(f"🔥 Component called with start_capture={start_capture}")
    print(f"🔥 Component returned: {component_value}")
    
    return component_value
