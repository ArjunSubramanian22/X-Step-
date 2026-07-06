from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ULCER_DIR = ROOT / "ulcer model"
HEATMAP_DIR = ROOT / "heatmap model"
ULCER_ARCHIVE = ULCER_DIR / "archive"
ULCER_GRADES = ("Grade 1", "Grade 2", "Grade 3", "Grade 4")
HEATMAP_NUM_CLASSES = 9
ULCER_NUM_CLASSES = 4
DEFAULT_IMAGE_SIZE = 224
DEFAULT_BATCH_SIZE = 32
DEFAULT_LR = 1e-4
DEFAULT_WEIGHT_DECAY = 1e-4
DEFAULT_PATIENCE = 7
DEFAULT_MAX_EPOCHS = 50
