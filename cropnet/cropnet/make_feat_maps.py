"""
Take an AE model and run inference to generate full feature maps for each of 
the 4 regions
"""

import argparse
import csv
import cv2
import logging
import numpy as np
import os
import shutil
import torch
import torch.nn as nn
import torch.nn.functional as F

from collections import OrderedDict

# pytorch imports
from torch.optim import Adam, SGD
from torch.utils.data import DataLoader
from torchvision.utils import save_image

# ml_utils imports
from general.utils import create_session_dir, retain_session_dir

# Local imports
from ae_model import CropNetCAE, CropNetFCAE, load_ae_model
from ae_trainer import AETrainer
from datasets import RGBPatchesCenter, TBChips
from utils import get_chip_bbox, get_features, get_bbox_from_file_path, \
        get_cdl_subregion, transform_cdl, normalize_feats

pe = os.path.exists
pj = os.path.join
HOME = os.path.expanduser("~")


g_hls_regions = ["ark", "ohio", "sd", "vai"]
g_cdl_regions = ["neAR", "nwOH", "seSD", "vai_crop"]


def _extract_session_dir(model_path):
    return os.path.dirname( os.path.dirname(model_path) )

def make_full_cdl_map(region, cfg):
    session_dir = _extract_session_dir(cfg["model_path"])
    feat_maps_dir = pj(session_dir, "feat_maps/cdl")
    if not pe(feat_maps_dir):
        os.makedirs(feat_maps_dir)
    feat_map = np.zeros((3000,3000)) # TODO
    d = cfg["labels_dir"]
    for p in [pj(d,f) for f in os.listdir(d) \
            if f.startswith("cdl_2016_"+region)]:
        feats = np.load(p)
        if feats.dtype != np.uint8:
            raise RuntimeError("Expecting type np.uint8 for %s, got %s" \
                    % (p, feats.dtype))
        bbox = get_bbox_from_file_path(p)
        sz = bbox[2] - bbox[0]
        feat_map[ bbox[0]:bbox[2], bbox[1]:bbox[3] ] = feats
    
    region_idx = g_cdl_regions.index(region)
    hls_name = g_hls_regions[region_idx]
    save_path = pj(feat_maps_dir, "%s_feat_map.npy" % (hls_name))
    np.save(save_path, feat_map)
    cv2.imwrite(save_path[:-4] + ".png", feat_map)
    
    feat_map,cat_dict = transform_cdl(feat_map)
    feat_map = (feat_map*255.0).astype(np.uint8)
    cv2.imwrite(save_path[:-4] + "_false_color.png", feat_map)

def make_full_feat_map(region, model, cfg):
    session_dir = _extract_session_dir(cfg["model_path"])
    feat_maps_dir = pj(session_dir, "feat_maps/hls")
    if not pe(feat_maps_dir):
        os.makedirs(feat_maps_dir)
    feat_map = np.zeros((3000,3000,3)) # TODO
    d = cfg["data_dir"]
    for p in [pj(d,f) for f in os.listdir(d) if f.startswith("hls_tb_"+region)]:
        tb_chips = TBChips(data_dir=d, tiles_per_cohort=1,
                data_file=os.path.basename(p))
        data_loader = DataLoader(dataset=tb_chips,
                shuffle=False,
                batch_size=cfg["batch_size"],
                num_workers=cfg["num_workers"])
        bbox = get_bbox_from_file_path(p)
        sz = bbox[2] - bbox[0]
        feats = get_features(model, data_loader, [0, 0, sz, sz])
        feat_map[ bbox[0]:bbox[2], bbox[1]:bbox[3], : ] = feats
    feat_map = normalize_feats(feat_map)
    save_path = pj(feat_maps_dir, "%s_feat_map.npy" % (region))
    np.save(save_path, feat_map)
    cv2.imwrite(save_path[:-4] + ".png", feat_map*255)

def main(args):
    cfg = vars(args)
    model = load_ae_model(args.model_path, args.model_name, chip_size=19,
            bneck_size=3, base_nchans=cfg["base_nchans"])
#    for region in g_hls_regions:
#        make_full_feat_map(region, model, cfg)
    for region in g_cdl_regions:
        make_full_cdl_map(region, cfg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model-name", type=str, default="CropNetCAE",
            choices=["CropNetCAE", "CropNetFCAE", "CropNetCVAE"])
    parser.add_argument("--model-path", type=str, 
            default=pj(HOME, "Training/cropnet/sessions/session_02/models/" \
                    "CropNetCAE.pkl"))
    parser.add_argument("-d", "--data-dir", type=str,
            default=pj(HOME, "Datasets/HLS/tb_data/all/hls"))
    parser.add_argument("-l", "--labels-dir", type=str,
            default=pj(HOME, "Datasets/HLS/tb_data/all/cdl"))
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--num-workers", type=int, default=8)
    parser.add_argument("--base-nchans", type=int, default=16)
    args = parser.parse_args()
    main(args)

