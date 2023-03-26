import logging
import cv2
import numpy as np
from abc import abstractmethod


class BaseTransformer:
    @abstractmethod
    def __call__(self, img):
        # [H, W, C]
        raise NotImplementedError


class ThresholdCrop(BaseTransformer):
    def __init__(self, lower_threshold: int, upper_threshold: int) -> None:
        self.lower = lower_threshold
        self.upper = upper_threshold

    def __call__(self, img):
        if len(img.shape) == 2:
            gray_img = img
        elif img.shape[2] == 3:
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif img.shape[2] == 4:
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        in_threshold = (gray_img >= self.lower) & (gray_img <= self.upper)  # type: ignore
        if not np.any(in_threshold): return img
        for h0 in range(in_threshold.shape[0]):
            if np.any(in_threshold[h0, :]): break
        for w0 in range(in_threshold.shape[1]):
            if np.any(in_threshold[:, w0]): break
        for h1 in range(in_threshold.shape[0] - 1, -1, -1):
            if np.any(in_threshold[h1, :]): break
        for w1 in range(in_threshold.shape[1] - 1, -1, -1):
            if np.any(in_threshold[:, w1]): break
        return img[h0:h1 + 1, w0:w1 + 1, ...]  # type: ignore


class DownSample(BaseTransformer):
    def __init__(self, screen_height: int, screen_width: int, interpolation: str = 'area') -> None:
        self.height = screen_height
        self.width = screen_width
        if interpolation == 'area': self.interpolation = cv2.INTER_AREA
        elif interpolation == 'lanczos': self.interpolation = cv2.INTER_LANCZOS4
        elif interpolation == 'nearest': self.interpolation = cv2.INTER_NEAREST
        elif interpolation == 'linear': self.interpolation = cv2.INTER_LINEAR
        elif interpolation == 'cubic': self.interpolation = cv2.INTER_CUBIC
        else: raise ValueError(f'Invalid interpolation {interpolation}')

    def __call__(self, img):
        if img.shape[0] > self.height or img.shape[1] > self.width:
            scaled_height = int(img.shape[0] * self.width / img.shape[1])
            scaled_width = int(img.shape[1] * self.height / img.shape[0])
            if scaled_height > self.height: shape = (scaled_width, self.height)
            else: shape = (self.width, scaled_height)
            img = cv2.resize(img, shape, interpolation=self.interpolation)
        return img


class ImagePipeline:
    def __init__(
        self,
        logger: logging.Logger,
        fixed_ext: str = '',
        jpeg_quality: int = 95,
        png_compression: int = 1,
    ) -> None:
        self.transforms = []
        self.fixed_ext = None if fixed_ext == '' else fixed_ext
        self.jpeg_quality = jpeg_quality
        self.png_compression = png_compression
        self.logger = logger.getChild('ImagePipeline')

    def append(self, transform: BaseTransformer):
        self.transforms.append(transform)

    def __call__(self, data, ext):
        img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None:
            self.logger.warning('Invalid image, skip')
            return data, ext
        for transform in self.transforms:
            img = transform(img)
        if self.fixed_ext: ext = self.fixed_ext
        _, data = cv2.imencode(ext, img, [
            cv2.IMWRITE_JPEG_QUALITY,
            self.jpeg_quality,
            cv2.IMWRITE_PNG_COMPRESSION,
            self.png_compression, ])
        data = data.tostring()
        return data, ext
