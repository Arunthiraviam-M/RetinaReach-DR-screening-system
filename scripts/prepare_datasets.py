from pathlib import Path
import random
import shutil


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"


# ============================================================
# SPLIT SETTINGS
# ============================================================

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

RANDOM_SEED = 42

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
}


# ============================================================
# FUNDUS DATASET
# ============================================================

# Your actual folder name is "colored_images"
FUNDUS_SOURCE = DATASET_DIR / "fundus" / "colored_images"

# Original folder name -> model class number
FUNDUS_CLASSES = {
    "No_DR": "0",
    "Mild": "1",
    "Moderate": "2",
    "Severe": "3",
    "Proliferate_DR": "4",
}


# ============================================================
# OCT DATASET
# ============================================================

# Your actual OCT image folder
OCT_SOURCE = DATASET_DIR / "oct" / "OCTDL"

OCT_CLASSES = [
    "AMD",
    "DME",
    "ERM",
    "NO",
    "RAO",
    "RVO",
    "VID",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_images(folder):
    """
    Get all supported image files from a class folder.
    """

    if not folder.exists():
        return []

    return [
        file
        for file in folder.iterdir()
        if file.is_file()
        and file.suffix.lower() in IMAGE_EXTENSIONS
    ]


def split_images(images):
    """
    Split images into:
        70% train
        15% validation
        15% test
    """

    images = list(images)

    random.shuffle(images)

    total = len(images)

    train_count = int(total * TRAIN_RATIO)
    val_count = int(total * VAL_RATIO)

    train_images = images[:train_count]

    val_images = images[
        train_count:train_count + val_count
    ]

    test_images = images[
        train_count + val_count:
    ]

    return train_images, val_images, test_images


def create_class_folders(base_directory, classes):
    """
    Create train/val/test folders for the supplied classes.
    """

    for split in ["train", "val", "test"]:

        for class_name in classes:

            folder = (
                base_directory
                / split
                / class_name
            )

            folder.mkdir(
                parents=True,
                exist_ok=True
            )


def copy_images(images, destination):
    """
    Copy images to the destination folder.
    """

    destination.mkdir(
        parents=True,
        exist_ok=True
    )

    for image in images:

        destination_file = destination / image.name

        shutil.copy2(
            image,
            destination_file
        )


# ============================================================
# FUNDUS DATASET PREPARATION
# ============================================================

def prepare_fundus():

    print()
    print("=" * 70)
    print("PREPARING FUNDUS DATASET")
    print("=" * 70)

    print(f"Source:")
    print(FUNDUS_SOURCE)

    # Check source folder
    if not FUNDUS_SOURCE.exists():

        raise FileNotFoundError(
            "\nFundus source folder was not found:\n"
            f"{FUNDUS_SOURCE}\n\n"
            "Please check that the folder is named exactly:\n"
            "colored_images"
        )

    # Create train/val/test folders
    create_class_folders(
        DATASET_DIR / "fundus",
        FUNDUS_CLASSES.values()
    )

    total_images = 0

    print()

    for source_class, target_class in FUNDUS_CLASSES.items():

        source_folder = (
            FUNDUS_SOURCE / source_class
        )

        # Check class folder
        if not source_folder.exists():

            print(
                f"WARNING: Folder not found: "
                f"{source_folder}"
            )

            continue

        # Get images
        images = get_images(
            source_folder
        )

        # Use fixed seed so the split is reproducible
        random.seed(
            RANDOM_SEED
        )

        train_images, val_images, test_images = (
            split_images(images)
        )

        # Destination folders
        train_folder = (
            DATASET_DIR
            / "fundus"
            / "train"
            / target_class
        )

        val_folder = (
            DATASET_DIR
            / "fundus"
            / "val"
            / target_class
        )

        test_folder = (
            DATASET_DIR
            / "fundus"
            / "test"
            / target_class
        )

        # Copy images
        copy_images(
            train_images,
            train_folder
        )

        copy_images(
            val_images,
            val_folder
        )

        copy_images(
            test_images,
            test_folder
        )

        total_images += len(images)

        print(
            f"{source_class:18s} "
            f"Total: {len(images):5d} | "
            f"Train: {len(train_images):5d} | "
            f"Val: {len(val_images):5d} | "
            f"Test: {len(test_images):5d}"
        )

    print()
    print(
        f"Total Fundus images: {total_images}"
    )


# ============================================================
# OCT DATASET PREPARATION
# ============================================================

def prepare_oct():

    print()
    print("=" * 70)
    print("PREPARING OCT DATASET")
    print("=" * 70)

    print("Source:")
    print(OCT_SOURCE)

    # Check source folder
    if not OCT_SOURCE.exists():

        raise FileNotFoundError(
            "\nOCT source folder was not found:\n"
            f"{OCT_SOURCE}\n\n"
            "Please check that the folder is named exactly:\n"
            "OCTDL"
        )

    # Create train/val/test folders
    create_class_folders(
        DATASET_DIR / "oct",
        OCT_CLASSES
    )

    total_images = 0

    print()

    for class_name in OCT_CLASSES:

        source_folder = (
            OCT_SOURCE / class_name
        )

        # Check class folder
        if not source_folder.exists():

            print(
                f"WARNING: Folder not found: "
                f"{source_folder}"
            )

            continue

        # Get images
        images = get_images(
            source_folder
        )

        # Fixed seed for reproducibility
        random.seed(
            RANDOM_SEED
        )

        train_images, val_images, test_images = (
            split_images(images)
        )

        # Destination folders
        train_folder = (
            DATASET_DIR
            / "oct"
            / "train"
            / class_name
        )

        val_folder = (
            DATASET_DIR
            / "oct"
            / "val"
            / class_name
        )

        test_folder = (
            DATASET_DIR
            / "oct"
            / "test"
            / class_name
        )

        # Copy images
        copy_images(
            train_images,
            train_folder
        )

        copy_images(
            val_images,
            val_folder
        )

        copy_images(
            test_images,
            test_folder
        )

        total_images += len(images)

        print(
            f"{class_name:8s} "
            f"Total: {len(images):5d} | "
            f"Train: {len(train_images):5d} | "
            f"Val: {len(val_images):5d} | "
            f"Test: {len(test_images):5d}"
        )

    print()
    print(
        f"Total OCT images: {total_images}"
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print()
    print("=" * 70)
    print("DATASET PREPARATION STARTED")
    print("=" * 70)

    print()
    print(f"Project:")
    print(PROJECT_ROOT)

    print()
    print(
        "Split ratio: "
        f"{TRAIN_RATIO:.0%} train / "
        f"{VAL_RATIO:.0%} validation / "
        f"{TEST_RATIO:.0%} test"
    )

    # Prepare Fundus
    prepare_fundus()

    # Prepare OCT
    prepare_oct()

    # Finished
    print()
    print("=" * 70)
    print("DATASET PREPARATION COMPLETED")
    print("=" * 70)

    print()
    print("Original datasets were NOT modified.")
    print("Images were copied into train/val/test folders.")

    print()
    print("Fundus classes:")
    print("  0 = No DR")
    print("  1 = Mild DR")
    print("  2 = Moderate DR")
    print("  3 = Severe DR")
    print("  4 = Proliferative DR")

    print()
    print("OCT classes:")
    print("  AMD")
    print("  DME")
    print("  ERM")
    print("  NO")
    print("  RAO")
    print("  RVO")
    print("  VID")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()