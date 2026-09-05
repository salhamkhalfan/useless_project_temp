<img width="1280" height="640" alt="git (1)" src="https://github.com/user-attachments/assets/8920b256-2ba8-4988-b824-5351134eb4bd" />



# Touchപുല്ല് 🎯


## Basic Details
### Team Name: The Crew


### Team Members
- Member 1: Fathima Afrah Peedikapparaben - KAHM Unity Women's College, Manjeri
- Member 2: Salha M Khalfan - KAHM Unity Women's College, Manjeri

### Project Description
*Touchപുല്ല്* is a scientifically unnecessary system that lets a leaf decide what you should watch. Upload a leaf, and our system analyzes its venation, converts it into a graph, derives a mathematical value, and uses that value to select *exactly one long-form YouTube video*. 🍃🎥

### The Problem (that doesn't exist)
Humans are suffering from an overlooked crisis: *having to decide what to watch on YouTube.* With millions of videos to choose from, making this decision is simply too much responsibility. Why decide for yourself when a leaf can do it for you?

### The Solution (that nobody asked for)
We outsourced your YouTube decision to an equation.

Upload a leaf → detect its veins → turn them into a graph → calculate its structural complexity → generate a unique value *R* → let *R* decide exactly one long-form YouTube video.

*No preferences. No recommendations. No second options.*
You don't choose the video.*The equation does.*
Because apparently, a leaf has better plans for your free time. 🍃

## Technical Details
### Technologies/Components Used
For Software:
- Python, JavaScript, HTML5 + CSS3, PowerShell / CMD
- FastAPI, Uvicorn
- OpenCV, scikit-image, sknw, NetworkX, NumPy, matplotlib, httpx, python-multipart, YouTube iframe embed API,Web Audio API
- YouTube Data API v3, Git / GitHub, Token launchers, Environment config, Persistent JSON cache

### Implementation
For Software:
# Installation
pip install -r requirements.txt

# Run
uvicorn app:app host 0.0.0.0    

### Project Documentation
For Software:

# Screenshots (Add at least 3)

![Landing page](images/landingPage.jpeg)
*The starting point of the experience. Users are invited to upload a leaf and let its venation determine what they will watch. The playful pixel-art nature theme reinforces the project's deliberately unnecessary idea: go outside, touch a leaf, and let mathematics choose your YouTube video.*

![Image Result](images/result1.jpeg)
*The journey from leaf to equation. After uploading a leaf, the system shows the original image, extracted vein skeleton, graph overlay, and cleaned graph. It then calculates the structural properties of the venation network and combines them into the final R value.*

![Link redirection](images/result2.jpeg)
*The final result of the leaf analysis. The system displays the detected graph statistics, including nodes, edges, connected components, cyclomatic number, total vein length, and the calculated R value. This value is then used to determine and display one long-form YouTube video.*

# Diagrams
![Workflow](
├── app.py                  ← WEB LAYER (FastAPI): upload, analyze, serve results
├── youtube.py              ← INTEGRATION: YouTube Data API + R→query + cache
├── main/
│   ├── vein_graph.py       ← PIPELINE DRIVER: process_leaf(), paths, orchestrator
│   ├── process.py          ← image prep: morphology blackhat/whitehat, thresholding, clean binary
│   ├── skeleton.py         ← skeletonize + prune + component filtering
│   └── graph_utils.py      ← graph build, largest comp, simplify, stats, visualization
├── templates/index.html    ← UI markup (pixel garden + dropzone + gallery)
├── static/                 ← style.css (theme), script.js (logic, sounds, lightbox)
├── images/                 ← input leaf photos
├── live_uploads/{job_id}/  ← per-request artifacts (input/skeleton/overlay/clean)
├── leaf-skeleton|leaf-graph-overlay|leaf-graph-clean|leaf-node|leaf-edges/
│                           ← batch pipeline output folders (threshold_test.py)
├── video_cache.json        ← leaf→video persistence (gitignored)
├── .env                    ← YOUTUBE_API_KEY (gitignored)
├── requirements.txt / run_web.bat / threshold_test.py
└── useless-env/            ← Python 3.12 venv
)
*Doomscrolling follows a modular pipeline that transforms a simple leaf photograph into a mathematically determined YouTube video. The FastAPI web layer handles uploads and results, while the image-processing pipeline cleans the image, extracts and prunes the vein skeleton, and converts the venation into a graph. Graph statistics are then used to calculate the R value, which is passed to the YouTube integration to generate a query and select exactly one long-form video. Processed images and video selections are cached for faster results and reproducibility.*

### Project Demo
# Video
https://drive.google.com/file/d/1wIaDNQmJFJKBzNtEDQH3VgPr_Xcu6uZe/view?usp=sharing
*A quick walkthrough of Touchപുല്ല്, showing the complete journey from uploading a leaf to getting a YouTube video chosen by its mathematical structure. The demo showcases the vein detection, graph generation, calculation of the R value, and the final long-form YouTube video selected based on the leaf.*

## Team Contributions
- Fathima Afrah Peedikapparamben: Leaf vein detection and graph extraction
- Salha M Khalfan: API, UI

---
Made with ❤️ at TinkerHub Useless Projects 

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--26-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)



