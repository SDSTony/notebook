# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.8.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + [markdown] id="Mp_NYLoZMcIf"
# # 4. RetinaNet
#

# + [markdown] id="osFFm5Qjc8gW"
# [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1hb5MB94nNjOvPKgq7p5-gXbz0Qi4BjZz?usp=sharing)

# + colab={"base_uri": "https://localhost:8080/", "height": 334} tags=["remove-input"] id="HbcoYV0uc7yr" executionInfo={"status": "ok", "timestamp": 1607650820645, "user_tz": -540, "elapsed": 775, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="a7a0774c-e12c-42e6-8d45-fde87668a057"
from IPython.display import HTML

HTML('<iframe width="560" height="315" src="https://www.youtube.com/embed/rkHc_Tzn810" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>')



# + [markdown] id="KK93nhnJfoyQ"
# 3장에서는 제공된 데이터에 augmentation을 가하는 방법과 데이터셋 클래스를 만드는 방법을 확인했습니다. 이번 장에서는 여기에 수정을 해주겠습니다. torchvision에서 제공하는 one-stage 모델인 RetinaNet을 활용해 의료용 마스크 검출 모델을 구축해보겠습니다. 
#
# 4.1절부터 4.3절까지는 2장과 3장에서 확인한 내용을 바탕으로 데이터를 불러오고 훈련용, 시험용 데이터로 나눈 후 데이터셋 클래스를 정의하겠습니다. 4.4절에서는 torchvision API를 활용하여 사전 훈련된 모델을 불러오겠습니다. 4.5절에서는 전이 학습을 통해 모델 학습을 진행한 후 4.6절에서 예측값 산출 및 모델 성능을 확인해보겠습니다. 

# + [markdown] id="hagQJQhNH3tx"
# ## 4.1 데이터 다운로드

# + [markdown] id="84tdB7_Lfrne"
# 모델링 실습을 위해 2.1절에 나온 코드를 활용하여 데이터를 불러오겠습니다.

# + id="TWRFeIewiogs" colab={"base_uri": "https://localhost:8080/"} executionInfo={"status": "ok", "timestamp": 1606505906985, "user_tz": -540, "elapsed": 7627, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="05d238ae-e4a6-4146-c1dc-4fa919a7ff9b"
# !git clone https://github.com/Pseudo-Lab/Tutorial-Book-Utils
# !python Tutorial-Book-Utils/PL_data_loader.py --data FaceMaskDetection
# !unzip -q Face\ Mask\ Detection.zip

# + [markdown] id="JzK1cPwJJu_d"
# ## 4.2 데이터 분리

# + [markdown] id="bTn5bLPVftSn"
# 3.3절에서 확인한 데이터 분리 방법을 활용하여 데이터를 분리하겠습니다. 

# + id="PHqwbdjycpUP" colab={"base_uri": "https://localhost:8080/"} executionInfo={"status": "ok", "timestamp": 1606506027461, "user_tz": -540, "elapsed": 721, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="f2481721-1cfa-4974-cdc1-b0d70309d5a7"
import os
import random
import numpy as np
import shutil

print(len(os.listdir('annotations')))
print(len(os.listdir('images')))

# !mkdir test_images
# !mkdir test_annotations


random.seed(1234)
idx = random.sample(range(853), 170)

for img in np.array(sorted(os.listdir('images')))[idx]:
    shutil.move('images/'+img, 'test_images/'+img)

for annot in np.array(sorted(os.listdir('annotations')))[idx]:
    shutil.move('annotations/'+annot, 'test_annotations/'+annot)

print(len(os.listdir('annotations')))
print(len(os.listdir('images')))
print(len(os.listdir('test_annotations')))
print(len(os.listdir('test_images')))

# + [markdown] id="S3aR-WPJGbqr"
# ## 4.3 데이터셋 클래스 정의
#

# + [markdown] id="AIFHVnmlfvSy"
# 파이토치 모델을 학습시키기 위해선 데이터셋 클래스를 정의해야 합니다. torchvision에서 제공하는 객체 탐지 모델을 학습시키기 위한 데이터셋 클래스의 `__getitem__` 메서드는 이미지 파일과 바운딩 박스 좌표를 반환 합니다. 데이터셋 클래스를 3장에서 활용한 코드를 응용해 아래와 같이 정의 하겠습니다. 

# + id="6AW5nZyNio-2"
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
from bs4 import BeautifulSoup
from PIL import Image
import cv2
import numpy as np
import time
import torch
import torchvision
from torch.utils.data import Dataset
from torchvision import transforms
from matplotlib import pyplot as plt
import os

def generate_box(obj):
    
    xmin = float(obj.find('xmin').text)
    ymin = float(obj.find('ymin').text)
    xmax = float(obj.find('xmax').text)
    ymax = float(obj.find('ymax').text)
    
    return [xmin, ymin, xmax, ymax]

def generate_label(obj):

    if obj.find('name').text == "with_mask":

        return 1

    elif obj.find('name').text == "mask_weared_incorrect":

        return 2

    return 0

def generate_target(file): 
    with open(file) as f:
        data = f.read()
        soup = BeautifulSoup(data, "html.parser")
        objects = soup.find_all("object")

        num_objs = len(objects)

        boxes = []
        labels = []
        for i in objects:
            boxes.append(generate_box(i))
            labels.append(generate_label(i))

        boxes = torch.as_tensor(boxes, dtype=torch.float32) 
        labels = torch.as_tensor(labels, dtype=torch.int64) 
        
        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        
        return target

def plot_image_from_output(img, annotation):
    
    img = img.cpu().permute(1,2,0)
    
    fig,ax = plt.subplots(1)
    ax.imshow(img)
    
    for idx in range(len(annotation["boxes"])):
        xmin, ymin, xmax, ymax = annotation["boxes"][idx]

        if annotation['labels'][idx] == 0 :
            rect = patches.Rectangle((xmin,ymin),(xmax-xmin),(ymax-ymin),linewidth=1,edgecolor='r',facecolor='none')
        
        elif annotation['labels'][idx] == 1 :
            
            rect = patches.Rectangle((xmin,ymin),(xmax-xmin),(ymax-ymin),linewidth=1,edgecolor='g',facecolor='none')
            
        else :
        
            rect = patches.Rectangle((xmin,ymin),(xmax-xmin),(ymax-ymin),linewidth=1,edgecolor='orange',facecolor='none')

        ax.add_patch(rect)

    plt.show()

class MaskDataset(Dataset):
    def __init__(self, path, transform=None):
        self.path = path
        self.imgs = list(sorted(os.listdir(self.path)))
        self.transform = transform
        
    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        file_image = self.imgs[idx]
        file_label = self.imgs[idx][:-3] + 'xml'
        img_path = os.path.join(self.path, file_image)
        
        if 'test' in self.path:
            label_path = os.path.join("test_annotations/", file_label)
        else:
            label_path = os.path.join("annotations/", file_label)

        img = Image.open(img_path).convert("RGB")
        target = generate_target(label_path)
        
        to_tensor = torchvision.transforms.ToTensor()

        if self.transform:
            img, transform_target = self.transform(np.array(img), np.array(target['boxes']))
            target['boxes'] = torch.as_tensor(transform_target)

        # tensor로 변경
        img = to_tensor(img)


        return img, target


def collate_fn(batch):
    return tuple(zip(*batch))

dataset = MaskDataset('images/')
test_dataset = MaskDataset('test_images/')

data_loader = torch.utils.data.DataLoader(dataset, batch_size=4, collate_fn=collate_fn)
test_data_loader = torch.utils.data.DataLoader(test_dataset, batch_size=2, collate_fn=collate_fn)

# + [markdown] id="e2kNQXFNL4Aw"
# 최종적으로 훈련용 데이터와 시험용 데이터를 batch 단위로 불러올 수 있게 `torch.utils.data.DataLoader` 함수를 활용해 `data_loader`와 `test_data_loader`를 각각 정의합니다. 

# + [markdown] id="nRrFZq0AOcN3"
# ## 4.4 모델 불러오기
#

# + [markdown] id="Ux0kyJv5fyES"
# `torchvision`에서는 각종 컴퓨터 비전 문제를 해결하기 위한 딥러닝 모델을 쉽게 불러올 수 있는 API를 제공합니다. `torchvision.models` 모듈을 활용하여 RetinaNet 모델을 불러오도록 하겠습니다. RetinaNet은 `torchvision` 0.8.0 이상에서 제공되므로, 아래 코드를 활용하여 `torchvision` 버전을 맞춰줍니다.

# + id="Cr8H6JLey_1E" colab={"base_uri": "https://localhost:8080/"} executionInfo={"status": "ok", "timestamp": 1606506425492, "user_tz": -540, "elapsed": 4943, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="5254f8cb-2cc4-4b8e-9ac3-4af141cbab27"
# !pip install torch==1.7.0+cu101 torchvision==0.8.1+cu101 torchaudio==0.7.0 -f https://download.pytorch.org/whl/torch_stable.html

# + id="TvElOoznuOo_"
import torchvision
import torch

# + id="3JGtQrFSvZD6" colab={"base_uri": "https://localhost:8080/", "height": 35} executionInfo={"status": "ok", "timestamp": 1606509502433, "user_tz": -540, "elapsed": 585, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="b5872089-8430-4eb6-9a8a-4073ad562651"
torchvision.__version__

# + [markdown] id="PCBtpaBmPaVL"
# `torchvision.__version__` 명령어를 통해 현재 cuda 10.1 버전에서 작동하는 `torchvision` 0.8.1 버전이 설치 됐음을 확인할 수 있습니다. 다음으로는 아래 코드를 실행하여 RetinaNet 모델을 불러옵니다. Face Mask Detection 데이터셋에 3개의 클래스가 존재하므로 num_classes 매개변수를 3으로 정의하고, 전이 학습을 할 것이기 때문에 backbone 구조는 사전 학습 된 가중치를, 그 외 가중치는 초기화 상태로 가져옵니다. backbone은 객체 탐지 데이터셋으로 유명한 Coco 데이터셋에 사전 학습 됐습니다.

# + id="1EUUU5E_s_oV"
retina = torchvision.models.detection.retinanet_resnet50_fpn(num_classes = 3, pretrained=False, pretrained_backbone = True)

# + [markdown] id="-3p2PLxpP8PQ"
# ## 4.5 전이 학습

# + [markdown] id="TpvFMGNff0Yn"
# 모델을 불러왔으면 아래 코드를 활용하여 전이 학습을 진행합니다. (코드 셀 나눠서 설명 더 추가해야함)

# + id="qBpMkUNVQQqo" colab={"base_uri": "https://localhost:8080/"} executionInfo={"status": "ok", "timestamp": 1606292618162, "user_tz": -540, "elapsed": 7577122, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="c43c5c67-0bf6-401a-bf05-f9f5bfb08633"
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

num_epochs = 30
retina.to(device)
    
# parameters
params = [p for p in retina.parameters() if p.requires_grad] # gradient calculation이 필요한 params만 추출
optimizer = torch.optim.SGD(params, lr=0.005,
                                momentum=0.9, weight_decay=0.0005)

len_dataloader = len(data_loader)

for epoch in range(num_epochs):
    start = time.time()
    retina.train()

    i = 0    
    epoch_loss = 0
    for images, targets in data_loader:
        images = list(image.to(device) for image in images)
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

        loss_dict = retina(images, targets) 

        losses = sum(loss for loss in loss_dict.values()) 

        i += 1

        optimizer.zero_grad()
        losses.backward()
        optimizer.step()
        
        epoch_loss += losses 
    print(epoch_loss, f'time: {time.time() - start}')

# + [markdown] id="uWdd-bPpRje0"
# 모델 재사용을 위해 아래 코드를 실행하여 학습된 가중치를 저장해줍니다. `torch.save` 함수를 활용해 지정한 위치에 학습된 가중치를 저장할 수 있습니다.

# + id="buEMhbtZRhSx"
torch.save(retina.state_dict(),f'retina_{num_epochs}.pt')

# + colab={"base_uri": "https://localhost:8080/"} id="YwOeuUCqGEc0" executionInfo={"status": "ok", "timestamp": 1606509535460, "user_tz": -540, "elapsed": 5341, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="7e8b02c1-9b32-4ba2-c173-3ce61753974a"
retina.load_state_dict(torch.load(f'retina_{num_epochs}.pt'))

# + [markdown] id="c-6mROA6boUr"
# 학습된 가중치를 불러올 때는 `load_state_dict`과 `torch.load`함수를 사용하면 됩니다. 만약 retina 변수를 새롭게 지정했을 경우, 해당 모델을 GPU 메모리에 올려주어야 GPU 연산이 가능합니다. 

# + id="apqJwlQGbi1E"
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
retina.to(device)


# + [markdown] id="5Yt8iHl7QHJj"
# ## 4.6 예측

# + [markdown] id="7Wd0wEgvozWK"
# 훈련이 마무리 되었으면, 예측 결과를 확인하도록 하겠습니다. test_data_loader에서 데이터를 불러와 모델에 넣어 학습 후, 예측된 결과와 실제 값을 각각 시각화 해보도록 하겠습니다. 우선 예측에 필요한 함수를 정의하겠습니다.

# + id="QNnJ31gVzch8"
def make_prediction(model, img, threshold):
    model.eval()
    preds = model(img)
    for id in range(len(preds)) :
        idx_list = []

        for idx, score in enumerate(preds[id]['scores']) :
            if score > threshold : #threshold 넘는 idx 구함
                idx_list.append(idx)

        preds[id]['boxes'] = preds[id]['boxes'][idx_list]
        preds[id]['labels'] = preds[id]['labels'][idx_list]
        preds[id]['scores'] = preds[id]['scores'][idx_list]


    return preds

# + [markdown] id="Ib8vthZOX5nt"
# `make_prediction` 함수에는 학습된 딥러닝 모델을 활용해 예측하는 알고리즘이 저장돼 있습니다. `threshold` 파라미터를 조정해 신뢰도가 일정 수준 이상의 바운딩 박스만 선택합니다. 보통 0.5 이상인 값을 최종 선택합니다. 다음으로는 for문을 활용해 `test_data_loader`에 있는 모든 데이터에 대해 예측을 실시하겠습니다.

# + colab={"base_uri": "https://localhost:8080/"} id="Xhb-l1gPSbXA" executionInfo={"status": "ok", "timestamp": 1606509709274, "user_tz": -540, "elapsed": 25283, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="b7542333-51d7-4eef-9879-b12135c6d8c8"
from tqdm import tqdm

labels = []
preds_adj_all = []
annot_all = []

for im, annot in tqdm(test_data_loader, position = 0, leave = True):
    im = list(img.to(device) for img in im)
    #annot = [{k: v.to(device) for k, v in t.items()} for t in annot]

    for t in annot:
        labels += t['labels']

    with torch.no_grad():
        preds_adj = make_prediction(retina, im, 0.5)
        preds_adj = [{k: v.to(torch.device('cpu')) for k, v in t.items()} for t in preds_adj]
        preds_adj_all.append(preds_adj)
        annot_all.append(annot)


# + [markdown] id="5WmaVxDmYn5Y"
# `tqdm` 함수를 활용해 진행 상황을 표츌하고 있습니다. 예측된 모든 값은 `preds_adj_all` 변수에 저장됐습니다. 다음으로는 실제 바운딩 박스와 예측한 바운딩 박스에 대한 시각화를 진행해보겠습니다.

# + colab={"base_uri": "https://localhost:8080/", "height": 1000, "output_embedded_package_id": "1rIbtuvTZx9YlR1RavfZLh0vXyZgGwV65"} id="0lFxRwSdSBwj" executionInfo={"status": "ok", "timestamp": 1606509717388, "user_tz": -540, "elapsed": 5151, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="f213a1c8-48d0-4bac-dd2e-a0034e33a148"
batch_i = 0
for im, annot in test_data_loader:
    for sample_i in range(len(im)) :
        print('true')
        plot_image_from_output(im[sample_i], annot[sample_i])
        print('pred')
        plot_image_from_output(im[sample_i], preds_adj_all[batch_i][sample_i])
    batch_i += 1
    if batch_i == 4:
        break

# + [markdown] id="NTvuyHGXZBBH"
# for문을 활용해 4개의 batch, 총 8개의 이미지에 대한 실제 값과 예측 값을 시각해 보았습니다. 마스크 착용자는 잘 탐지하고 있는 것을 관측하고 있으며, 마스크 미착용자에 대해서는 가끔씩 마스크를 올바르게 착용하지 않는 것으로 탐지하는 것을 볼 수 있습니다. 전반적인 모델 성능을 평가하기 위해 mean Average Precision (mAP)를 산출해보겠습니다. mAP는 객체 탐지 모델을 평가할 때 사용하는 지표입니다. (추가 설명 입력)
#
# 데이터 다운로드시 불러왔던 Tutorial-Book-Utils 폴더 내에는 utils_ObjectDetection.py 파일이 있습니다. 해당 모듈 내에 있는 함수를 활용해 mAP를 산출해보겠습니다. 우선 utils_ObjectDetection.py 모듈을 불러옵니다.

# + colab={"base_uri": "https://localhost:8080/"} id="hGOG2JGPZ2Qg" executionInfo={"status": "ok", "timestamp": 1606509731197, "user_tz": -540, "elapsed": 712, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="56f2e93e-bd9c-4de6-da3a-a72745045795"
# %cd Tutorial-Book-Utils/
import utils_ObjectDetection as utils

# + id="nQLausRKTB16"
sample_metrics = []
for batch_i in range(len(preds_adj_all)):
    sample_metrics += utils.get_batch_statistics(preds_adj_all[batch_i], annot_all[batch_i], iou_threshold=0.5) 

# + [markdown] id="YP56-gyddy9P"
# batch 별 mAP를 산출하는데 필요한 정보를 `sample_metrics`에 저장 후 `ap_per_class`함수를 활용해 mAP를 산출합니다. 

# + colab={"base_uri": "https://localhost:8080/"} id="uxsYNiXacYxQ" executionInfo={"status": "ok", "timestamp": 1606509884671, "user_tz": -540, "elapsed": 759, "user": {"displayName": "\uc548\uc131\uc9c4", "photoUrl": "https://lh3.googleusercontent.com/a-/AOh14GiCjgkN_MvtrSUHRuFvstrWm6fhi5cf7CKd2UHYAw=s64", "userId": "00266029492778998652"}} outputId="11f2317b-3269-4b31-b901-fab685c5ba58"
true_positives, pred_scores, pred_labels = [torch.cat(x, 0) for x in list(zip(*sample_metrics))]  # 배치가 전부 합쳐짐
precision, recall, AP, f1, ap_class = utils.ap_per_class(true_positives, pred_scores, pred_labels, torch.tensor(labels))
mAP = torch.mean(AP)
print(f'mAP : {mAP}')
print(f'AP : {AP}')

# + [markdown] id="njTGWnKGd8l-"
# 결과를 해석하면 0번 클래스인 마스크를 미착용한 객체에 대해서는 0.7684 AP를 보이며 1번 클래스인 마스크 착용 객체에 대해서는 0.9188 AP를 보이고, 2번 클래스인 마스크를 올바르게 착용하지 않은 객체에 대해서는 0.06 AP를 보입니다. (결과 해석 내용 보완하기)
#
# 지금까지 RetinaNet에 대한 전이 학습을 실시해 의료용 마스크 탐지 모델을 만들어 보았습니다. 다음 장에서는 Two-Stage Detector인 Faster R-CNN을 활용해 탐지 성능을 높여보겠습니다. 
