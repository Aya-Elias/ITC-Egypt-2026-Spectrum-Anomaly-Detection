"""PyInstaller hook for Streamlit builds."""

from PyInstaller.utils.hooks import collect_data_files

# Keep Streamlit static/runtime files bundled when desktop packaging is enabled.
datas = collect_data_files("streamlit")
