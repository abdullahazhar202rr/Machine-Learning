# Shop People Counter

## Project Overview

This project implements a **Shop People Counter** system using the YOLOv8 model for object detection and the SORT (Simple Online and Realtime Tracking) algorithm for tracking people in a video feed. The system counts the number of people entering and exiting a shop by detecting crossings over two defined lines (entry and exit) in the video frame. The counts are saved to a CSV file for further analysis. This project is developed by **Abdullah Azhar** and is part of a public portfolio to showcase computer vision and tracking capabilities.

## Features

- **Object Detection**: Utilizes YOLOv8 (`best.pt` model, trained on the "people" class) to detect individuals in a video feed.
- **Tracking**: Implements the SORT algorithm to track detected people across frames, assigning unique IDs.
- **Counting Mechanism**: Counts entries and exits based on people crossing predefined entry (green) and exit (red) lines.
- **Data Logging**: Saves timestamps, entry counts, exit counts, and the number of people inside the shop to a `shop_counts.csv` file.
- **Real-Time Visualization**: Displays the video feed with bounding boxes, track IDs, entry/exit lines, and real-time counts.

## Prerequisites

To run this project, ensure you have the following installed:

- Python 3.8+
- OpenCV (`cv2`)
- Ultralytics YOLO (`ultralytics`)
- NumPy
- SciPy
- FilterPy
- Pandas
- A webcam or video input device

You can install the required dependencies using:

```bash
pip install opencv-python ultralytics numpy scipy filterpy pandas
```

Additionally, download the pre-trained YOLOv8 model (`best.pt`) trained on the "people" class and place it in the project directory.

## How It Works

1. **Video Input**: The system captures video from a webcam (`cv2.VideoCapture(0)`).
2. **Detection**: YOLOv8 detects people in each frame with a confidence threshold of 0.5.
3. **Tracking**: The SORT algorithm assigns and tracks unique IDs for detected people across frames.
4. **Counting**:
   - Two horizontal lines are defined: a green entry line (top) and a red exit line (bottom).
   - The system tracks the centroid of each detected person and detects when they cross these lines in specific directions:
     - Crossing the green line downward initiates an "entering" state.
     - Crossing the red line downward from the "entering" state increments the entry count.
     - Crossing the red line upward initiates an "exiting" state.
     - Crossing the green line upward from the "exiting" state increments the exit count.
5. **Data Storage**: Each time an entry or exit is recorded, the system logs the timestamp, entry count, exit count, and number of people inside (`entries - exits`) to `shop_counts.csv`.
6. **Visualization**: The video feed displays bounding boxes, track IDs, entry/exit lines, and current counts.

## Usage

1. Clone this repository:

   ```bash
   git clone https://github.com/<your-username>/shop-people-counter.git
   cd shop-people-counter
   ```

2. Ensure the `best.pt` YOLOv8 model file is in the project directory.

3. Run the script:

   ```bash
   python shop_counter.py
   ```

4. The system will open a webcam feed and display the tracking and counting in real-time.

5. Press `q` to quit the application.

## Output

- **Video Output**: A window titled "Shop People Counter" shows the live feed with:
  - Green entry line and red exit line.
  - Bounding boxes around detected people with their track IDs.
  - Real-time counts for entries, exits, and people inside.
- **CSV Output**: A file named `shop_counts.csv` is created/updated with columns:
  - `timestamp`: Date and time of the event.
  - `entries`: Cumulative number of entries.
  - `exits`: Cumulative number of exits.
  - `inside`: Current number of people inside (entries - exits).

## Configuration

- **Model**: Replace `best.pt` with your own YOLOv8 model if needed.
- **Line Positions**: Adjust `entry_line_y` and `exit_line_y` in the code to position the entry and exit lines based on your video frame. They are currently set to 40% and 60% of the frame height, respectively.
- **SORT Parameters**:
  - `max_age`: Maximum number of frames a track can persist without updates (default: 20).
  - `min_hits`: Minimum number of detections required to start a track (default: 3).
  - `iou_threshold`: IOU threshold for associating detections with tracks (default: 0.3).

## Credits

- **Author**: Abdullah Azhar
- **YOLOv8**: Developed by Ultralytics (https://github.com/ultralytics/ultralytics)
- **SORT Algorithm**: Based on the implementation by Alex Bewley (https://github.com/abewley/sort)
- **Libraries**: OpenCV, NumPy, SciPy, FilterPy, Pandas


## Notes

- This repository is public and part of Abdullah Azhar's portfolio to demonstrate expertise in computer vision and object tracking.

For any issues or contributions, please open an issue or submit a pull request on GitHub.