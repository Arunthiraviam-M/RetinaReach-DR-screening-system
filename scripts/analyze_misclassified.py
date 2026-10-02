import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from PIL import Image


CLASS_NAMES = [
    "No DR",
    "Mild DR",
    "Moderate DR",
    "Severe DR",
    "Proliferative DR",
]

NUM_CLASSES = 5
IMG_SIZE = 300


def build_model():
    model = models.efficientnet_b3(weights=None)

    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, NUM_CLASSES)

    return model


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-dir",
        required=True
    )

    parser.add_argument(
        "--model",
        required=True
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    model_path = Path(args.model)

    test_dir = data_dir / "test"

    output_dir = (
        Path("..")
        / "ml_models"
        / "evaluation"
        / "misclassified"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 60)
    print("MISCLASSIFIED FUNDUS IMAGE ANALYSIS")
    print("=" * 60)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Device: {device}")

    transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    dataset = datasets.ImageFolder(
        test_dir,
        transform=transform
    )

    loader = DataLoader(
        dataset,
        batch_size=4,
        shuffle=False,
        num_workers=0
    )

    model = build_model()

    checkpoint = torch.load(
        model_path,
        map_location=device
    )

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(
            checkpoint["model_state_dict"]
        )
    else:
        model.load_state_dict(checkpoint)

    model.to(device)
    model.eval()

    total = 0
    correct = 0
    misclassified = 0

    print("\nChecking test images...")

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            probabilities = torch.softmax(
                outputs,
                dim=1
            )

            predictions = torch.argmax(
                probabilities,
                dim=1
            )

            for i in range(len(labels)):

                total += 1

                true_class = labels[i].item()
                predicted_class = predictions[i].item()

                if true_class == predicted_class:
                    correct += 1
                    continue

                misclassified += 1

                original_path = Path(
                    dataset.samples[
                        total - 1
                    ][0]
                )

                filename = original_path.name
                stem = original_path.stem
                suffix = original_path.suffix

                confidence = (
                    probabilities[i][predicted_class]
                    .item() * 100
                )

                new_filename = (
                    f"actual_{true_class}_"
                    f"pred_{predicted_class}_"
                    f"conf_{confidence:.1f}_"
                    f"{stem}{suffix}"
                )

                output_path = (
                    output_dir / new_filename
                )

                original_image = Image.open(
                    original_path
                ).convert("RGB")

                original_image.save(
                    output_path
                )

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    print(f"Total test images       : {total}")
    print(f"Correct predictions     : {correct}")
    print(f"Misclassified images    : {misclassified}")

    print(
        f"\nMisclassified images saved to:\n"
        f"{output_dir.resolve()}"
    )

    print("\nFilename format:")
    print(
        "actual_X_pred_Y_conf_Z_image.jpg"
    )

    print("\nClass numbers:")

    for i, name in enumerate(CLASS_NAMES):
        print(f"{i} = {name}")


if __name__ == "__main__":
    main()cf