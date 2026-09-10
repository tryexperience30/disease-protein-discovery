"""Ranked prediction table with sorting, filtering, and CSV download."""

import streamlit as st
import pandas as pd
from app.config import METHOD_ORDER


def render_prediction_table(pred_df, disease_name):
    """Display interactive ranked prediction table with controls.

    Parameters
    ----------
    pred_df : pd.DataFrame
        Output of predict_for_disease() — ranked by Combined Score.
    disease_name : str
    """
    if pred_df.empty:
        st.warning("No predictions available for this disease.")
        return

    col_top, col_download = st.columns([3, 1])

    with col_top:
        top_k = st.slider("Show top K predictions", 10, min(500, len(pred_df)),
                           value=min(50, len(pred_df)), step=10)

    display_df = pred_df.head(top_k).copy()

    display_cols = ["Gene ID"] + METHOD_ORDER + ["Combined Score"]
    available_cols = [c for c in display_cols if c in display_df.columns]
    show_df = display_df[available_cols].copy()

    format_dict = {m: "{:.4f}" for m in METHOD_ORDER if m in show_df.columns}
    format_dict["Combined Score"] = "{:.4f}"

    st.dataframe(
        show_df.style.format(format_dict).background_gradient(
            subset=["Combined Score"], cmap="YlOrRd"
        ),
        use_container_width=True,
        height=min(35 * top_k + 38, 600),
    )

    with col_download:
        csv = pred_df.to_csv(index=True)
        st.download_button(
            "Download Full CSV",
            csv,
            file_name=f"predictions_{disease_name.replace(' ', '_')}.csv",
            mime="text/csv",
        )
