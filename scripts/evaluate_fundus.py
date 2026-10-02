import argparse
import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models


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


def calculate_metrics(confusion_matrix):
    metrics = []

    total_correct = sum(
        confusion_matrix[i][i] for i in range(NUM_CLASSES)
    )

    total_samples = sum(
        sum(row) for row in confusion_matrix
    )

    accuracy = total_correct / total_samples if total_samples else 0.0

    f1_scores = []

    for i, class_name in enumerate(CLASS_NAMES):
        tp = confusion_matrix[i][i]

        fp = sum(
            confusion_matrix[row][i]
            for row in range(NUM_CLASSES)
            if row != i
        )

        fn = sum(
            confusion_matrix[i][col]
            for col in range(NUM_CLASSES)
            if col != i
        )

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0

        if precision + recall:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0

        f1_scores.append(f1)

        metrics.append({
            "class": class_name,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(confusion_matrix[i]),
        })

    macro_f1 = sum(f1_scores) / NUM_CLASSES

    return accuracy, macro_f1, metrics


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-dir",
        required=True,
        help="Fundus dataset directory"
    )

    parser.add_argument(
        "--model",
        required=True,
        help="Path to trained model"
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    model_path = Path(args.model)

    test_dir = data_dir / "test"

    print("=" * 60)
    print("FUNDUS TEST SET EVALUATION")
    print("=" * 60)

    print(f"Test dataset : {test_dir}")
    print(f"Model        : {model_path}")

    if not test_dir.exists():
        raise FileNotFoundError(
            f"Test directory not found: {test_dir}"
        )

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}"
        )

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Device       : {device}")

    test_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    test_dataset = datasets.ImageFolder(
        test_dir,
        transform=test_transform
    )

    print(f"Test images  : {len(test_dataset)}")

    print("\nClass mapping:")

    for index, class_name in enumerate(test_dataset.classes):
        print(f"  {index} -> {class_name}")

    test_loader = DataLoader(
        test_dataset,
        batch_size=4,
        shuffle=False,
        num_workers=0,
    )

    print("\nLoading model...")

    model = build_model()

    checkpoint = torch.load(
        model_path,
        map_location=device
    )

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model = model.to(device)
    model.eval()

    print("Model loaded successfully.")

    confusion_matrix = [
        [0 for _ in range(NUM_CLASSES)]
        for _ in range(NUM_CLASSES)
    ]

    total = 0
    correct = 0

    print("\nEvaluating test set...")

    with torch.no_grad():

        for images, labels in test_loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            predictions = torch.argmax(outputs, dim=1)

            total += labels.size(0)
            correct += (predictions == labels).sum().item()

            for true_label, predicted_label in zip(
                labels.cpu().numpy(),
                predictions.cpu().numpy()
            ):
                confusion_matrix[
                    int(true_label)
                ][
                    int(predicted_label)
                ] += 1

    accuracy, macro_f1, class_metrics = calculate_metrics(
        confusion_matrix
    )

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    print(f"Test Accuracy : {accuracy * 100:.2f}%")
    print(f"Test Macro-F1 : {macro_f1 * 100:.2f}%")

    print("\nPer-class results:")

    for metric in class_metrics:
        print(
            f"\n{metric['class']}"
            f"\n  Precision : {metric['precision'] * 100:.2f}%"
            f"\n  Recall    : {metric['recall'] * 100:.2f}%"
            f"\n  F1        : {metric['f1'] * 100:.2f}%"
            f"\n  Images    : {metric['support']}"
        )

    print("\nConfusion Matrix")
    print("Rows = Actual")
    print("Columns = Predicted\n")

    print(" " * 20 + " ".join(
        f"{i:^8}" for i in range(NUM_CLASSES)
    ))

    for i, row in enumerate(confusion_matrix):
        print(
            f"{CLASS_NAMES[i]:<20}"
            + " ".join(f"{value:^8}" for value in row)
        )

    results = {
        "model": str(model_path),
        "test_dataset": str(test_dir),
        "test_images": len(test_dataset),
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "class_metrics": class_metrics,
        "confusion_matrix": confusion_matrix,
    }

    output_path = (
        model_path.parent / "fundus_test_results.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print(
        f"\nResults saved to:\n{output_path}"
    )

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()