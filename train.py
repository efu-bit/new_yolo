import os, shutil
import ultralytics
from ultralytics import YOLO

print('[0/6] Ultralytics checks...')
ultralytics.checks()

print('\n[1/6] Loading base model yolo11n.pt ...')
model = YOLO('yolo11n.pt')

print('\n[2/6] Training (epochs=3, imgsz=640) on HomeObjects-3K.yaml ...')
results = model.train(data='HomeObjects-3K.yaml', epochs=3, imgsz=640)

save_dir = getattr(model, 'trainer', None).save_dir if getattr(model, 'trainer', None) else None
print(f'[INFO] save_dir: {save_dir}')
assert save_dir and os.path.isdir(save_dir), f'Unexpected save_dir: {save_dir}'

best_path = os.path.join(save_dir, 'weights', 'best.pt')
print(f'[INFO] best.pt: {best_path}')
assert os.path.exists(best_path), f'best.pt not found at {best_path}'

print('\n[3/6] Quick prediction with the trained model ...')
modelp = YOLO(best_path)
_ = modelp.predict('https://ultralytics.com/assets/home-objects-sample.jpg', save=True)
print('[OK] Prediction done.')

print('\n[4/6] Exporting ONNX (optional) ...')
modele = YOLO(best_path)
_ = modele.export(format='onnx')
print('[OK] Export complete.')

dst = '/home/efu/decor/decor-detective-main/backend/best.pt'
print(f"\n[5/6] Copying best.pt to {dst} ...")
shutil.copy2(best_path, dst)
print('[OK] Copied best.pt.')

print('\n[6/6] Verifying file ...')
size_mb = os.path.getsize(dst) / (1024*1024)
print(f'[OK] backend/best.pt size = {size_mb:.2f} MB')
print('\n✅ All steps completed.')