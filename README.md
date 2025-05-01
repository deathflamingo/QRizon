# QRizon

**QRizon** is a file to video converter that transforms any file into a sequence of QR codes and encodes them into a video stream.

---

## Features

- Converts files to a video with QR codes (2 per frame)
- Encodes metadata (filename, size) into the video
- Decodes the video back into the original file
- Can be stored on YouTube, downloaded, and restore all data

---

## Requirements

- Python 3.7+
- Dependencies:
  - `qrcode`
  - `opencv-python`
  - `numpy`
  - `Pillow`
  - `pyzbar`

Install them with:

```bash
pip install qrcode opencv-python numpy Pillow pyzbar
```

---

## Usage

Encode a file into a QR video

```bash
python QRizon.py encode -i <input_file> -o <output_video.mp4>
```

Example:

```bash
python QRizon.py encode -i secret.zip -o out.mp4
```

Decode a QR video back to a file

```bash
python QRizon.py decode -i <input_video.mp4> -o <output_directory>
```

Example:

```bash
python QRizon.py decode -i out.mp4 -o ./recovered/
```

## How It Works

### Encoding:

- File is base64-encoded and split into fixed-size chunks.
- Each chunk is encoded as a QR code.
- Two QR codes are embedded per video frame.
- Metadata (filename and size) is embedded in the initial QR(s).

### Decoding:

- Video frames are scanned for QR codes using pyzbar.
- Metadata is parsed to reconstruct the file correctly.
- All chunks are joined, base64-decoded, and saved.

### Notes

- Each frame holds 2 QR codes (300×300 px each) side-by-side.
- Default chunk size per QR: 200 characters.
- From my testing, YouTube compression does NOT kill the video when using low error- but, if you want to switch to high error correction make sure you increase the frame size, 300x300 isn't enough
