import os
import streamlit.components.v1 as components

# 🔥 Tên folder chứa index.html
_COMPONENT_DIR = os.path.join(os.path.dirname(__file__), "webcam_component")

# 🔥 Khai báo component đúng đường dẫn
webcam_component = components.declare_component(
    "webcam_component",
    path=_COMPONENT_DIR
)

def capture_component(start_capture=False, key="webcam"):
    return webcam_component(
        start_capture=start_capture,
        default=None,
        key=key
    )
