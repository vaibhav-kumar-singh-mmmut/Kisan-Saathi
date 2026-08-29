import os
import torch
import torchvision
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split
import torch.nn as nn
import torch.optim as optim
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights

def setup_dataset():
    """
    Downloads the PlantVillage dataset from GitHub instead of Kaggle.
    """
    repo_url = "https://github.com/spMohanty/PlantVillage-Dataset"
    target_dir = "PlantVillage-Dataset"
    
    if not os.path.exists(target_dir):
        print(f"Downloading dataset from {repo_url}...")
        os.system(f"git clone {repo_url}")
    else:
        print("Dataset already downloaded.")
        
    # The color images are usually in 'raw/color'
    data_path = os.path.join(target_dir, "raw", "color")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Expected dataset path not found: {data_path}. Please check the repository structure.")
        
    return data_path

def train_model():
    print("PyTorch Version:", torch.__version__)
    
    # 1. Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # 2. Get dataset path
    data_path = setup_dataset()
    
    # 3. Data Augmentation and Normalization
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                             std=[0.229, 0.224, 0.225]) # Standard ImageNet normalization
    ])

    # 4. Load Dataset
    print("Loading dataset...")
    full_dataset = datasets.ImageFolder(root=data_path, transform=transform)
    num_classes = len(full_dataset.classes)
    print(f"Found {len(full_dataset)} images belonging to {num_classes} classes.")

    # Split into train/val
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    batch_size = 32
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

    # 5. Initialize Model (MobileNetV3)
    print("Initializing MobileNetV3...")
    model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
    
    # Modify the final classifier layer for our number of classes
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)
    model = model.to(device)

    # 6. Loss and Optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 7. Training Loop
    num_epochs = 5
    print("Starting training...")
    
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        
        for i, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
            if (i + 1) % 50 == 0:
                print(f"Epoch [{epoch+1}/{num_epochs}], Step [{i+1}/{len(train_loader)}], Loss: {loss.item():.4f}")
                
        # Validation
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
                
        val_acc = 100 * correct / total
        print(f"Epoch [{epoch+1}/{num_epochs}] Validation Accuracy: {val_acc:.2f}%")

    # 8. Export to ONNX
    print("Training complete. Exporting to ONNX...")
    model.eval()
    dummy_input = torch.randn(1, 3, 224, 224, device=device)
    onnx_path = "crop_disease_model.onnx"
    
    torch.onnx.export(
        model, 
        dummy_input, 
        onnx_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    
    print(f"Model successfully exported to {onnx_path}")
    
    # Save classes JSON
    import json
    with open("classes.json", "w") as f:
        json.dump(full_dataset.classes, f)
    print("Class mapping saved to classes.json")

if __name__ == "__main__":
    train_model()
