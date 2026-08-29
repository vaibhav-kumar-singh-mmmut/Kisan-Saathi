# 🌾 Kisan Saathi — ML Model Training & Datasets

## Why the Initial Model had Limitations
The baseline **PlantVillage** dataset contains **54,306 images of isolated leaves on plain laboratory backgrounds**. 
In real Indian farm settings, smartphones capture:
- Variable outdoor sunlight & shadows
- Complex background soil, weeds, hands holding leaves
- Stems, roots, tubers, and whole plants (e.g. potatoes, wheat spikes, paddy panicles)
- Crops like Mustard, Wheat Rust, Rice Blast, and Sugarcane

---

## Recommended Additional Datasets for High Real-World Accuracy

1. **PlantDoc Dataset (IIT Delhi & Cornell)**:
   - Contains **2,569 in-field smartphone photos** taken under natural lighting across 13 species and 27 disease classes in real Indian fields.
   - GitHub: `https://github.com/pratikkayal/PlantDoc-Dataset`

2. **CropPest & Agricultural Disease (AI Challenger)**:
   - **50,000+ agricultural disease images** with disease severity levels (early, medium, severe).

3. **FieldPlant (Zenodo)**:
   - **5,170 field-captured images** taken by farmers with mobile phones.

4. **Background / Negative Class**:
   - Including a `Background_Without_Leaves` folder with images of soil, human hands, tools, and non-plants so the network explicitly learns not to guess crop diseases on random objects.

---

## How to Retrain the Model

### Option A: Free GPU on Google Colab (Fastest & Recommended)
1. Open [Google Colab](https://colab.research.google.com/).
2. Click **Upload** and select [`ml-model/train_colab.ipynb`](file:///c:/Users/mrala/Desktop/Kisan-Saathi/Kisan-Saathi/ml-model/train_colab.ipynb).
3. Set Runtime to **T4 GPU** (`Runtime > Change runtime type > T4 GPU`).
4. Click **Run All** (`Runtime > Run all`).
5. Colab will train for 15 epochs with MobileNetV3-Large, Cosine Annealing, and Field Augmentations, then automatically download the new `crop_disease_model.onnx` and `classes.json`.
6. Replace the files in `ml-model/` and restart the backend!

### Option B: Local Training
Run the new training script:
```bash
python ml-model/train_advanced.py
```
