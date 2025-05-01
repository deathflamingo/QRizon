import qrcode
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pyzbar.pyzbar as pyzbar
import math
import os
import json
import base64

QR_SIZE_PIXELS = 300        
BORDER_PIXELS = 20          # Border around each QR code
PADDING_PIXELS = 40         # Padding between the two QR codes
FRAME_RATE = 30             
CODEC = 'mp4v'              
CHUNK_SIZE = 200            # Characters per QR code (after base64)
METADATA_CHUNK_SIZE = 1000  
METADATA_MARKER = "QR_FILE_METADATA:"  

FRAME_WIDTH = QR_SIZE_PIXELS * 2 + PADDING_PIXELS + BORDER_PIXELS * 2
FRAME_HEIGHT = QR_SIZE_PIXELS + BORDER_PIXELS * 2

def file_to_video(input_filepath, output_video_path):
    try:
        with open(input_filepath, 'rb') as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode('ascii')
        file_size = len(raw)
        file_filename = os.path.basename(input_filepath)
        print(f"Encoding file: {file_filename} ({file_size} bytes) -> {len(b64)} base64 chars")

        metadata = {"filename": file_filename, "size": file_size}
        metadata_str = METADATA_MARKER + json.dumps(metadata)
        metadata_chunks = [metadata_str[i:i+METADATA_CHUNK_SIZE]
                           for i in range(0, len(metadata_str), METADATA_CHUNK_SIZE)]
        print(f"Metadata split into {len(metadata_chunks)} QR codes.")

        data_chunks = [b64[i:i+CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)]
        print(f"Base64 data split into {len(data_chunks)} chunks of up to {CHUNK_SIZE} chars.")

        all_chunks = metadata_chunks + data_chunks
        num_qrs = len(all_chunks)
        num_frames = math.ceil(num_qrs / 2)
        print(f"Total QR codes: {num_qrs}, frames (2 per frame): {num_frames}")
        fourcc = cv2.VideoWriter_fourcc(*CODEC)
        out = cv2.VideoWriter(output_video_path, fourcc, FRAME_RATE, (FRAME_WIDTH, FRAME_HEIGHT))
        if not out.isOpened():
            raise IOError(f"Cannot open video writer for {output_video_path}")

        # Generate frames
        for i in range(num_frames):
            frame_img = Image.new('RGB', (FRAME_WIDTH, FRAME_HEIGHT), 'white')
            qr_positions = [ (BORDER_PIXELS, BORDER_PIXELS),
                             (BORDER_PIXELS + QR_SIZE_PIXELS + PADDING_PIXELS, BORDER_PIXELS) ]
            for j in range(2):
                idx = i*2 + j
                if idx < num_qrs:
                    chunk = all_chunks[idx]
                    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
                    qr.add_data(chunk)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
                    img = img.resize((QR_SIZE_PIXELS, QR_SIZE_PIXELS), Image.Resampling.NEAREST)
                    frame_img.paste(img, qr_positions[j])
            frame = cv2.cvtColor(np.array(frame_img), cv2.COLOR_RGB2BGR)
            out.write(frame)
        out.release()
        print(f"Video saved to {output_video_path}")

    except Exception as e:
        print(f"Encoding error: {e}")

def video_to_file(input_video_path, output_dir):
    try:
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video {input_video_path}")

        metadata_parts = []
        data_parts = []
        metadata_read = False
        output_filename = None
        expected_size = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # extract two QR regions
            regions = [ frame[BORDER_PIXELS:BORDER_PIXELS+QR_SIZE_PIXELS,
                               BORDER_PIXELS:BORDER_PIXELS+QR_SIZE_PIXELS],
                        frame[BORDER_PIXELS:BORDER_PIXELS+QR_SIZE_PIXELS,
                               BORDER_PIXELS+QR_SIZE_PIXELS+PADDING_PIXELS:
                               BORDER_PIXELS+2*QR_SIZE_PIXELS+PADDING_PIXELS] ]
            for region in regions:
                qrs = pyzbar.decode(region)
                for qr in qrs:
                    text = qr.data.decode('ascii')
                    if not metadata_read and text.startswith(METADATA_MARKER):
                        metadata_parts.append(text[len(METADATA_MARKER):])
                    elif not metadata_read:
                        full_meta = ''.join(metadata_parts)
                        meta = json.loads(full_meta)
                        output_filename = meta.get('filename', 'recovered')
                        expected_size = meta.get('size')
                        print(f"Metadata: {output_filename}, {expected_size} bytes")
                        metadata_read = True
                        data_parts.append(text)
                    else:
                        data_parts.append(text)
        cap.release()
        full_b64 = ''.join(data_parts)
        raw = base64.b64decode(full_b64)
        if expected_size and len(raw) != expected_size:
            print(f"Warning: decoded size {len(raw)} != expected {expected_size}")
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, output_filename or 'recovered')
        with open(out_path, 'wb') as f:
            f.write(raw)
        print(f"File restored to {out_path}")

    except Exception as e:
        print(f"Decoding error: {e}")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='mode', required=True)
    e = sp.add_parser('encode'); e.add_argument('-i','--input',required=True); e.add_argument('-o','--output',required=True)
    d = sp.add_parser('decode'); d.add_argument('-i','--input',required=True); d.add_argument('-o','--output',required=True)
    args = p.parse_args()
    if args.mode == 'encode':
        file_to_video(args.input, args.output)
    else:
        video_to_file(args.input, args.output)

