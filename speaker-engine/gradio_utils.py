"""Gradio streaming helpers (UI layer only; no ML logic)."""
import gradio as gr


def gradio_skip_final():
    """Tell Gradio not to update the non-streaming output on this step."""
    return gr.skip()


def adapt_legacy_streaming_pairs(generator):
    """Map (stream_bytes, None|(sr, wav)) yields to Gradio-safe pairs."""
    for stream_chunk, full_audio in generator:
        if full_audio is None:
            yield stream_chunk, gradio_skip_final()
        else:
            yield stream_chunk, full_audio
