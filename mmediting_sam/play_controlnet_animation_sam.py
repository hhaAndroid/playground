import argparse
import os

import cv2
import numpy as np
from mmedit.edit import MMEdit
from mmengine import MODELS, Config
from mmengine.registry import init_default_scope
from segment_anything import SamPredictor, sam_model_registry
from tqdm import tqdm

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')


def generate_animation(video, save_path, prompt, negative_prompt, width,
                       height):
    editor = MMEdit(model_name='controlnet_animation')

    editor.infer(
        video=video,
        prompt=prompt,
        negative_prompt=negative_prompt,
        controlnet_conditioning_scale=0.7,
        image_width=width,
        image_height=height,
        save_path=save_path)


def generate_background(config, width, height):
    StableDiffuser = MODELS.build(config.model)
    StableDiffuser = StableDiffuser.to('cuda')
    back_ground_image = StableDiffuser.infer(
        config.bg_prompt, width=width, height=height, seed=config.bg_seed)
    back_ground_image = back_ground_image['samples'][0]

    return back_ground_image


def replace_background_with_sam(config, back_ground_image):
    # load sam
    sam = sam_model_registry['vit_h'](checkpoint=config.sam_checkpoint)
    predictor = SamPredictor(sam)

    # load image file names
    frame_files = os.listdir(config.middle_video_frame_path)
    frame_files = [
        os.path.join(config.middle_video_frame_path, f) for f in frame_files
    ]
    frame_files.sort()
    all_images = []
    for frame in frame_files:
        frame_extension = os.path.splitext(frame)[1]
        if frame_extension in IMAGE_EXTENSIONS:
            all_images.append(frame)

    if not os.path.exists(config.final_video_frame_path):
        os.makedirs(config.final_video_frame_path)

    point_coord = np.array(config.point_coord)
    point_label = [1] * len(point_coord)

    for ind in tqdm(range(len(all_images))):
        image_np = cv2.imread(all_images[ind])
        predictor.set_image(image=image_np)

        masks, _, _ = predictor.predict(
            point_coords=point_coord, point_labels=point_label)
        masks = np.float32(masks)
        masks = masks.transpose((1, 2, 0))

        gray = cv2.cvtColor(masks, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY)

        bg = np.asarray(back_ground_image)
        bg = cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)
        nb = np.expand_dims(binary, axis=2)
        nm = np.repeat(nb, repeats=3, axis=2)
        result = image_np * nm + bg * (1 - nm)

        save_name = os.path.join(config.final_video_frame_path,
                                 all_images[ind].split('/')[-1])
        cv2.imwrite(save_name, result)


def parse_args():
    parser = argparse.ArgumentParser(
        'Demo for playing controlnet animation with Segment-Anything-',
        add_help=True)
    parser.add_argument(
        '--config',
        type=str,
        default='configs/play_controlnet_animation_sam_config.py',
        help='path to config file contains `model` cfg of the detector')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    config_path = args.config

    # 0. load config and init mmediting
    config = Config.fromfile(config_path).copy()
    init_default_scope('mmedit')

    # 1. generate animation with mmediting controlnet animation
    generate_animation(
        video=config.source_video_frame_path,
        save_path=config.middle_video_frame_path,
        prompt=config.prompt,
        negative_prompt=config.negative_prompt,
        width=config.width,
        height=config.height)

    # 2. generate background with mmediting stable diffusion
    back_ground_image = generate_background(
        config, width=config.width, height=config.height)

    # 3. replace background with mask generated by sam
    replace_background_with_sam(config, back_ground_image)