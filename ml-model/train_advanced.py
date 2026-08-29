"""
Advanced Unified Crop Disease Model Training Script
Merges PlantVillage (54k lab images) + PlantDoc (2.5k real Indian farm smartphone photos)
+ Negative background class into a unified training pipeline.
"""
import os
import json
import shutil
import numpy as np
from PIL import Image
import torch
import torchvision
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split
import torch.nn as nn
import torch.optim as optim
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights

PLANTDOC_TO_PLANTVILLAGE = {
    "Apple Scab Leaf": "Apple___Apple_scab",
    "Apple leaf": "Apple___healthy",
    "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Bell_pepper leaf spot": "Pepper,_bell___Bacterial_spot",
    "Bell_pepper leaf": "Pepper,_bell___healthy",
    "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry_(including_sour)___healthy",
    "Corn Gray leaf spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn leaf blight": "Corn_(maize)___Northern_Leaf_Blight",
    "Corn rust leaf": "Corn_(maize)___Common_rust_",
    "Grape leaf black rot": "Grape___Black_rot",
    "Grape leaf": "Grape___healthy",
    "Peach leaf": "Peach___healthy",
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf late blight": "Potato___Late_blight",
    "Potato leaf": "Potato___healthy",
    "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",
    "Strawberry leaf": "Strawberry___healthy",
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",
    "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato leaf": "Tomato___healthy",
    "Tomato mold leaf": "Tomato___Leaf_Mold",
}

def prepare_unified_dataset(pv_path="PlantVillage-Dataset/raw/color", doc_path="PlantDoc-Dataset", output_dir="unified_dataset"):
    """Merges PlantVillage and PlantDoc datasets into a single unified structure with negative class."""
    os.makedirs(output_dir, exist_ok=True)

    if os.path.exists(pv_path):
        print(f"Merging PlantVillage images from {pv_path}...")
        for cls_name in os.listdir(pv_path):
            src_cls_dir = os.path.join(pv_path, cls_name)
            if os.path.isdir(src_cls_dir):
                dest_cls_dir = os.path.join(output_dir, cls_name)
                os.makedirs(dest_cls_dir, exist_ok=True)
                for fname in os.listdir(src_cls_dir):
                    if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                        shutil.copy2(os.path.join(src_cls_dir, fname), os.path.join(dest_cls_dir, f"pv_{fname}"))

    if os.path.exists(doc_path):
        print(f"Merging PlantDoc images from {doc_path}...")
        for split in ["train", "test"]:
            split_dir = os.path.join(doc_path, split)
            if os.path.exists(split_dir):
                for doc_cls in os.listdir(split_dir):
                    target = PLANTDOC_TO_PLANTVILLAGE.get(doc_cls)
                    if target:
                        dest_cls_dir = os.path.join(output_dir, target)
                        os.makedirs(dest_cls_dir, exist_ok=True)
                        doc_src = os.path.join(split_dir, doc_cls)
                        for fname in os.listdir(doc_src):
                            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                                shutil.copy2(os.path.join(doc_src, fname), os.path.join(dest_cls_dir, f"doc_{split}_{fname}"))

    # Negative background class
    bg_dir = os.path.join(output_dir, "Background_Without_Leaves")
    os.makedirs(bg_dir, exist_ok=True)
    for i in range(100):
        color_base = np.random.choice(["soil", "wall", "skin", "gray"])
        if color_base == "soil":
            base_rgb = np.random.randint(60, 110, size=(224, 224, 3), dtype=np.uint8)
        elif color_base == "wall":
            base_rgb = np.random.randint(180, 240, size=(224, 224, 3), dtype=np.uint8)
        elif color_base == "skin":
            base_rgb = np.array([210, 160, 140], dtype=np.uint8) + np.random.randint(-15, 15, size=(224, 224, 3), dtype=np.int16).clip(0, 255).astype(np.uint8)
        else:
            base_rgb = np.random.randint(90, 160, size=(224, 224, 3), dtype=np.uint8)
        Image.fromarray(base_rgb).save(os.path.join(bg_dir, f"synth_bg_{i}.jpg"))

    print(f"Dataset preparation complete. Saved to {output_dir}")
    return output_dir

def get_transforms():
    """Heavy field augmentation pipeline for real-world smartphone photos."""
    train_transform = transforms.Compose([
        transforms.Resize((240, 240)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(degrees=25),
        transforms.ColorJitter(brightness=0.25, contrast=0.25, saturation=0.25, hue=0.08),
        transforms.RandomAffine(degrees=15, translate=(0.1, 0.1), scale=(0.85, 1.15)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.2))
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    return train_transform, val_transform

def train_advanced_model(
    unified_dir="unified_dataset",
    epochs=15,
    batch_size=32,
    learning_rate=0.0005,
    onnx_output="crop_disease_model.onnx",
    classes_output="classes.json"
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using compute device: {device}")

    if not os.path.exists(unified_dir):
        prepare_unified_dataset(output_dir=unified_dir)

    train_transform, val_transform = get_transforms()

    print(f"Loading dataset from {unified_dir}...")
    full_dataset = datasets.ImageFolder(root=unified_dir, transform=train_transform)
    num_classes = len(full_dataset.classes)
    print(f"Loaded {len(full_dataset)} images across {num_classes} classes.")

    train_size = int(0.85 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

    print("Building MobileNetV3-Large backbone with pretrained weights...")
    model = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.DEFAULT)
    
    in_features = model.classifier[0].in_features
    model.classifier = nn.Sequential(
        nn.Linear(in_features, 1024),
        nn.Hardswish(),
        nn.Dropout(p=0.3),
        nn.Linear(1024, num_classes)
    )
    model = model.to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_acc = 0.0

    print("Starting training with Multi-Dataset & Cosine Annealing scheduler...")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        
        for step, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            if (step + 1) % 100 == 0:
                print(f"Epoch [{epoch+1}/{epochs}] Step [{step+1}/{len(train_loader)}] Loss: {loss.item():.4f}")

        scheduler.step()

        # Validation
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (preds == labels).sum().item()

        val_acc = 100.0 * correct / total
        print(f"--- Epoch [{epoch+1}/{epochs}] Validation Accuracy: {val_acc:.2f}% (LR: {scheduler.get_last_lr()[0]:.6f}) ---")

        if val_acc > best_acc:
            best_acc = val_acc
            print("New Best Accuracy! Saving checkpoint...")
            torch.save(model.state_dict(), "best_model.pth")

    print(f"\nTraining Complete. Best Accuracy: {best_acc:.2f}%. Exporting to ONNX...")
    model.load_state_dict(torch.load("best_model.pth"))
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224, device=device)
    torch.onnx.export(
        model,
        dummy_input,
        onnx_output,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}}
    )
    print(f"ONNX model exported to {onnx_output}")

    with open(classes_output, "w") as f:
        json.dump(full_dataset.classes, f, indent=2)
    print(f"Classes saved to {classes_output}")

if __name__ == "__main__":
    train_advanced_model()
