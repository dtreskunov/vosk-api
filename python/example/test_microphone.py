#!/usr/bin/env python3

import logging
import json
import sys
from pyaudio import PyAudio, Stream, paInt16
from contextlib import contextmanager, ExitStack
from typing import Generator, Iterator
from vosk import Model, KaldiRecognizer, SpkModel


@contextmanager
def _pyaudio() -> Iterator[PyAudio]:
    p = PyAudio()
    try:
        yield p
    finally:
        logging.info('Terminating PyAudio object')
        p.terminate()


@contextmanager
def _pyaudio_open_stream(p: PyAudio, *args, **kwargs) -> Iterator[Stream]:
    s = p.open(*args, **kwargs)
    try:
        yield s
    finally:
        logging.info('Closing PyAudio Stream')
        s.close()


def listen(model: Model, spk_model: SpkModel = None, speech_chunk_sec: float = 0.5, buffer_sec: float = 1):
    with ExitStack() as stack:
        rate = model.SampleFrequency()
        if spk_model:
            rec = KaldiRecognizer(model, spk_model, rate)
        else:
            rec = KaldiRecognizer(model, rate)
        p = stack.enter_context(_pyaudio())
        s = stack.enter_context(_pyaudio_open_stream(p,
                                                     format=paInt16,
                                                     channels=1,
                                                     rate=rate,
                                                     input=True,
                                                     frames_per_buffer=int(rate * buffer_sec)))
        while True:
            data = s.read(int(rate * speech_chunk_sec))
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                logging.info(res)
            else:
                res = json.loads(rec.PartialResult())
                logging.info(res)


def main(argv):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--model', help='Model path. Download and extract a model from https://github.com/alphacep/kaldi-android-demo/releases',
        type=lambda path: Model(path))
    parser.add_argument(
        '--spk-model', help='Speaker model path. Download and extract a model from https://github.com/alphacep/kaldi-android-demo/releases',
        type=lambda path: SpkModel(path))
    args = parser.parse_args()
    try:
        listen(args.model, args.spk_model)
    except KeyboardInterrupt:
        exit(0)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
    main(sys.argv)
