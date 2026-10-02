from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, models, transforms


NUM_CLASSES = 5
IMG_SIZE = 300

CLASS_NAMES = [
    "No DR",
    "Mild DR",
    "Moderate DR",
    "Severe DR",
    "Proliferative DR",
]


def build_model():
    print("Loading EfficientNet-B3...")

    model = models.efficientnet_b3(
        weights=models.EfficientNet_B3_Weights.IMAGENET1K_V1
    )

    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(
        in_features,
        NUM_CLASSES
    )

    return model


def get_dataloaders(data_dir, batch_size):

    data_dir = Path(data_dir)

    train_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),

        transforms.RandomHorizontalFlip(
            p=0.5
        ),

        transforms.RandomRotation(
            15
        ),

        transforms.ColorJitter(
            brightness=0.2,
            contrast=0.2
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])

    train_ds = datasets.ImageFolder(
        data_dir / "train",
        transform=train_transform
    )

    val_ds = datasets.ImageFolder(
        data_dir / "val",
        transform=val_transform
    )

    print(f"Training images   : {len(train_ds)}")
    print(f"Validation images : {len(val_ds)}")
    print(f"Classes           : {train_ds.classes}")

    # --------------------------------------------------
    # BALANCED SAMPLING
    # --------------------------------------------------

    labels = torch.tensor(
        train_ds.targets,
        dtype=torch.long
    )

    class_counts = torch.bincount(
        labels,
        minlength=NUM_CLASSES
    ).float()

    class_weights = 1.0 / class_counts

    sample_weights = class_weights[labels]

    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(train_ds),
        replacement=True
    )

    print("\nBalanced sampling enabled.")

    print("\nOriginal class distribution:")

    for i in range(NUM_CLASSES):
        print(
            f"{i} - {CLASS_NAMES[i]:18s}: "
            f"{int(class_counts[i])} images"
        )

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        sampler=sampler,
        num_workers=0
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0
    )

    return (
        train_ds,
        val_ds,
        train_loader,
        val_loader,
        class_counts
    )


def calculate_metrics(
    predictions,
    labels
):

    predictions = torch.tensor(
        predictions
    )

    labels = torch.tensor(
        labels
    )

    accuracy = (
        (predictions == labels)
        .sum()
        .item()
        / max(len(labels), 1)
    )

    f1_scores = []

    for class_id in range(NUM_CLASSES):

        tp = (
            (predictions == class_id)
            & (labels == class_id)
        ).sum().item()

        fp = (
            (predictions == class_id)
            & (labels != class_id)
        ).sum().item()

        fn = (
            (predictions != class_id)
            & (labels == class_id)
        ).sum().item()

        precision = tp / max(
            tp + fp,
            1
        )

        recall = tp / max(
            tp + fn,
            1
        )

        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = (
                2
                * precision
                * recall
                / (precision + recall)
            )

        f1_scores.append(f1)

    macro_f1 = (
        sum(f1_scores)
        / NUM_CLASSES
    )

    return (
        accuracy,
        macro_f1,
        f1_scores
    )


def evaluate(
    model,
    loader,
    device
):

    model.eval()

    predictions = []
    labels = []

    with torch.no_grad():

        for images, targets in loader:

            images = images.to(device)
            targets = targets.to(device)

            outputs = model(images)

            preds = outputs.argmax(
                dim=1
            )

            predictions.extend(
                preds.cpu().tolist()
            )

            labels.extend(
                targets.cpu().tolist()
            )

    accuracy, macro_f1, f1_scores = calculate_metrics(
        predictions,
        labels
    )

    return (
        accuracy,
        macro_f1,
        f1_scores
    )


def train(args):

    data_dir = Path(
        args.data_dir
    )

    device = torch.device(
        args.device
    )

    print("\n==============================")
    print("RETINASCAN FUNDUS TRAINING")
    print("==============================")

    print(
        f"Dataset : {data_dir.resolve()}"
    )

    print(
        f"Device  : {device}"
    )

    print(
        f"Epochs  : {args.epochs}"
    )

    print(
        f"Batch   : {args.batch_size}"
    )

    (
        train_ds,
        val_ds,
        train_loader,
        val_loader,
        class_counts
    ) = get_dataloaders(
        data_dir,
        args.batch_size
    )

    model = build_model().to(device)

    # IMPORTANT:
    # Weighted sampling already balances the classes.
    # Therefore we use normal CrossEntropyLoss here
    # instead of applying class weights again.
    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr
    )

    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.epochs
    )

    output_path = Path(
        args.output
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    best_macro_f1 = -1.0

    history = []

    print("\nStarting training...\n")

    for epoch in range(args.epochs):

        model.train()

        running_loss = 0.0

        for batch_index, (
            images,
            labels
        ) in enumerate(
            train_loader,
            start=1
        ):

            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            loss.backward()

            optimizer.step()

            running_loss += (
                loss.item()
                * images.size(0)
            )

            if batch_index % 20 == 0:

                print(
                    f"Epoch {epoch + 1}/{args.epochs} "
                    f"| Batch {batch_index}/{len(train_loader)}"
                )

        scheduler.step()

        train_loss = (
            running_loss
            / len(train_loader.dataset)
        )

        (
            val_accuracy,
            val_macro_f1,
            val_f1_scores
        ) = evaluate(
            model,
            val_loader,
            device
        )

        print(
            f"\nEpoch {epoch + 1}/{args.epochs}"
        )

        print(
            f"Train Loss    : {train_loss:.4f}"
        )

        print(
            f"Val Accuracy  : {val_accuracy:.4f}"
        )

        print(
            f"Val Macro-F1   : {val_macro_f1:.4f}"
        )

        print("\nPer-class F1:")

        for i, f1 in enumerate(
            val_f1_scores
        ):

            print(
                f"  {CLASS_NAMES[i]:18s}: "
                f"{f1:.4f}"
            )

        history.append({
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "val_accuracy": val_accuracy,
            "val_macro_f1": val_macro_f1,
            "per_class_f1": {
                CLASS_NAMES[i]:
                val_f1_scores[i]
                for i in range(NUM_CLASSES)
            }
        })

        if val_macro_f1 > best_macro_f1:

            best_macro_f1 = val_macro_f1

            torch.save(
                model.state_dict(),
                output_path
            )

            print(
                f"\n✓ Best model saved → "
                f"{output_path}"
            )

    history_path = (
        output_path.parent
        / "training_history.json"
    )

    with open(
        history_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history,
            f,
            indent=2
        )

    print("\n==============================")
    print("TRAINING COMPLETE")
    print("==============================")

    print(
        f"Best Validation Macro-F1: "
        f"{best_macro_f1:.4f}"
    )

    print(
        f"Model saved to: "
        f"{output_path.resolve()}"
    )

    print(
        f"History saved to: "
        f"{history_path.resolve()}"
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-dir",
        type=str,
        required=True
    )

    parser.add_argument(
        "--output",
        type=str,
        default="../ml_models/weights/dr_classifier.pt"
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=10
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=4
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4
    )

    parser.add_argument(
        "--device",
        type=str,
        default=(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )
    )

    args = parser.parse_args()

    train(args)