"""
This file holds the trainer for the segmentation network.
"""

import argparse
import os
import platform

# pytorch includes
import torch
import torch.nn as nn
import torchvision as tv
from torch.utils.data import DataLoader

# local includes
from datasets import RGBPatches
from cropunet import CropUNet

pe = os.path.exists
pj = os.path.join
HOME = os.path.expanduser("~")
if platform.node() == "matt-XPS-8900":
    DATA = HOME
else:
    DATA = "/media/data"


def main(args):
    dataset = RGBPatches(args.data_dir_or_file, args.labels_dir_or_file,
            mode="train")
    model = CropSeg(256, args.num_classes)



def _test_main(args):
    dataset = RGBPatches(args.data_dir_or_file, args.labels_dir_or_file,
            mode="train")
    data_loader = DataLoader(dataset,
            batch_size=4,
            num_workers=1,
            shuffle=False)
    model = CropUNet()
    criterion = nn.CrossEntropyLoss
    iterator = iter(data_loader)
    patches,labels = next(iterator)
    yhat = model(patches)
    loss = criterion(patches, yhat)
    print(loss)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true",
            help="If set, just run the test code")
    parser.add_argument("--ae-model-path", type=str, 
            default=pj(HOME, "Training/cropnet/sessions/session_10/models/" \
                    "pretrained.pkl"))
    parser.add_argument("-d", "--data-dir-or-file", type=str,
            default=pj(HOME, "Training/cropnet/sessions/session_07/feats.npy"))
    parser.add_argument("-l", "--labels-dir-or-file", type=str,
            default=pj(DATA, "Datasets/HLS/test_imgs/cdl/" \
                    "cdl_2016_neAR_0_0_500_500.npy"))
    parser.add_argument("-s", "--image-size", type=int, default=256)
    parser.add_argument("--nc", "--num-classes", dest="num_classes", type=int,
            default=4)
    parser.add_argument("--no-cuda", dest="use_cuda", action="store_false")
    args = parser.parse_args()
    if args.test:
        _test_main(args)
    else:
        main(args)

