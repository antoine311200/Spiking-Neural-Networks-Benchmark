from utils import set_seed

import numpy as np

from torch.utils.data import DataLoader
from torch.utils.data import random_split
from typing import Callable, Optional

import torchvision.transforms as transforms

from spikingjelly.datasets.shd import SpikingHeidelbergDigits
from spikingjelly.datasets.shd import SpikingSpeechCommands
from spikingjelly.datasets import pad_sequence_collate

import torch
import torchaudio
from torchaudio.transforms import Spectrogram, MelScale, AmplitudeToDB, Resample
from torchaudio.datasets.speechcommands import SPEECHCOMMANDS
from torchvision import transforms
from torch.utils.data import Dataset
import augmentations

import torch
import torchvision
import torchvision.transforms as transforms

from sklearn import datasets
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

class RNoise(object):

  def __init__(self, sig):
    self.sig = sig

  def __call__(self, sample):
    noise = np.abs(np.random.normal(0, self.sig, size=sample.shape).round())
    return sample + noise

    def __call__(self, sample):
        noise = np.abs(np.random.normal(0, self.sig, size=sample.shape).round())
        return sample + noise


class TimeNeurons_mask_aug(object):
    def __init__(self, config):
        self.config = config

  def __init__(self, config):
    self.config = config


  def __call__(self, x, y):
    # Sample shape: (time, neurons)
    for sample in x:
      # Time mask
      if np.random.uniform() < self.config.TN_mask_aug_proba:
        mask_size = np.random.randint(0, self.config.time_mask_size)
        ind = np.random.randint(0, sample.shape[0] - self.config.time_mask_size)
        sample[ind:ind+mask_size, :] = 0

            # Neuron mask
            if np.random.uniform() < self.config.TN_mask_aug_proba:
                mask_size = np.random.randint(0, self.config.neuron_mask_size)
                ind = np.random.randint(
                    0, sample.shape[1] - self.config.neuron_mask_size
                )
                sample[:, ind : ind + mask_size] = 0

        return x, y


class CutMix(object):
  """
  Apply Spectrogram-CutMix augmentaiton which only cuts patch across time axis unlike
  typical Computer-Vision CutMix. Applies CutMix to one batch and its shifted version.

  """

  def __init__(self, config):
    self.config = config


  def __call__(self, x, y):

    # x shape: (batch, time, neurons)
    # Go to L-1, no need to augment last sample in batch (for ease of coding)

    for i in range(x.shape[0]-1):
      # other sample to cut from
      j = i+1

      if np.random.uniform() < self.config.cutmix_aug_proba:
        lam = np.random.uniform()
        cut_size = int(lam * x[j].shape[0])

    def __call__(self, x, y):
        # x shape: (batch, time, neurons)
        # Go to L-1, no need to augment last sample in batch (for ease of coding)

        for i in range(x.shape[0] - 1):
            # other sample to cut from
            j = i + 1

            if np.random.uniform() < self.config.cutmix_aug_proba:
                lam = np.random.uniform()
                cut_size = int(lam * x[j].shape[0])

                ind = np.random.randint(0, x[i].shape[0] - cut_size)

                x[i][ind : ind + cut_size, :] = x[j][ind : ind + cut_size, :]

                y[i] = (1 - lam) * y[i] + lam * y[j]

        return x, y


class Augs(object):
    def __init__(self, config):
        self.config = config
        self.augs = [TimeNeurons_mask_aug(config), CutMix(config)]

  def __init__(self, config):
    self.config = config
    self.augs = [TimeNeurons_mask_aug(config), CutMix(config)]

  def __call__(self, x, y):
    for aug in self.augs:
      x, y = aug(x, y)

    return x, y

        return x, y


def SHD_dataloaders(config):
    set_seed(config.seed)

    train_dataset = BinnedSpikingHeidelbergDigits(
        config.datasets_path,
        config.n_bins,
        train=True,
        data_type="frame",
        duration=config.time_step,
    )
    test_dataset = BinnedSpikingHeidelbergDigits(
        config.datasets_path,
        config.n_bins,
        train=False,
        data_type="frame",
        duration=config.time_step,
    )

    # train_dataset, valid_dataset = random_split(train_dataset, [0.8, 0.2])

    train_loader = DataLoader(
        train_dataset,
        collate_fn=pad_sequence_collate,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=4,
    )
    # valid_loader = DataLoader(valid_dataset, collate_fn=pad_sequence_collate, batch_size=config.batch_size)
    test_loader = DataLoader(
        test_dataset,
        collate_fn=pad_sequence_collate,
        batch_size=config.batch_size,
        num_workers=4,
    )

    return train_loader, test_loader


def IRIS_dataloaders(config):
    set_seed(config.seed)

    # Load the Iris dataset from scikit-learn
    iris = datasets.load_iris()
    X = iris.data
    y = iris.target

    # Split the data into train, validation, and test sets
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42
    )

    # Convert NumPy arrays to PyTorch tensors
    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.int64)
    X_val = torch.tensor(X_val, dtype=torch.float32)
    y_val = torch.tensor(y_val, dtype=torch.int64)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.int64)

    # Create TensorDatasets for train, validation, and test sets
    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)
    test_dataset = TensorDataset(X_test, y_test)

    # Create DataLoader objects
    batch_size = config.batch_size
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    valid_loader = DataLoader(val_dataset, batch_size=batch_size)
    test_loader = DataLoader(test_dataset, batch_size=batch_size)

    return train_loader, valid_loader, test_loader


class Flatten(torch.nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, tensor: torch.Tensor) -> torch.Tensor:
        """ """
        return tensor.flatten()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(mean={self.mean}, std={self.std})"

class FlattenColor(torch.nn.Module):

    def __init__(self):
        super().__init__()

    def forward(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        """
        return tensor.reshape(-1, 32)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(mean={self.mean}, std={self.std})"



def cifar10_dataloaders(config, shuffle=True, valid_size=0.2, num_workers=4):

  set_seed(config.seed)
  batch_size = config.batch_size

  transform = transforms.Compose([
      transforms.ToTensor(),  # Converts images to tensors
      transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),  # Normalize image pixel values
      Flatten(),
  ])

    transform = transforms.Compose(
        [
            transforms.ToTensor(),  # Converts images to tensors
            transforms.Normalize(
                (0.5, 0.5, 0.5), (0.5, 0.5, 0.5)
            ),  # Normalize image pixel values
            Flatten(),
            Repeat(config.max_delay),
        ]
    )

    # Download CIFAR-10 dataset if not already downloaded
    train_dataset = torchvision.datasets.CIFAR10(
        root=config.datasets_path, train=True, transform=transform, download=True
    )
    test_dataset = torchvision.datasets.CIFAR10(
        root=config.datasets_path, train=False, transform=transform, download=True
    )

  # Create data loaders for training, validation, and testing
  train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size,
                                              num_workers=0, pin_memory=True,)
  valid_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size,
                                              num_workers=0, pin_memory=True,)
  test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False,
                                            num_workers=0, pin_memory=True,)

  # Print the dataset sizes and shapes
  print(f"Train dataset size: {len(train_loader.sampler)}")
  print(f"Validation dataset size: {len(valid_loader.sampler)}")
  print(f"Test dataset size: {len(test_loader.sampler)}")
  print(f"Image shape: {train_dataset[0][0].shape}")
  print(f"Number of classes: {len(train_dataset.classes)}")

  return train_loader, valid_loader, test_loader

def cifar10_line_dataloaders(config, shuffle=True, valid_size=0.2, num_workers=4):

  set_seed(config.seed)
  batch_size = config.batch_size

  transform = transforms.Compose([
      transforms.ToTensor(),  # Converts images to tensors
      transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),  # Normalize image pixel values,
      FlattenColor(),
  ])

  # Download CIFAR-10 dataset if not already downloaded
  train_dataset = torchvision.datasets.CIFAR10(root=config.datasets_path, train=True, transform=transform, download=True)
  test_dataset = torchvision.datasets.CIFAR10(root=config.datasets_path, train=False, transform=transform, download=True)

  # Split the training dataset into training and validation sets
  num_train = len(train_dataset)
  if shuffle:
      torch.manual_seed(42)  # For reproducibility
      indices = torch.randperm(num_train)

  # Create data loaders for training, validation, and testing
  train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size,
                                              num_workers=0, pin_memory=True,)
  valid_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size,
                                              num_workers=0, pin_memory=True,)
  test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False,
                                            num_workers=0, pin_memory=True,)

  # Print the dataset sizes and shapes
  print(f"Train dataset size: {len(train_loader.sampler)}")
  print(f"Validation dataset size: {len(valid_loader.sampler)}")
  print(f"Test dataset size: {len(test_loader.sampler)}")
  print(f"Image shape: {train_dataset[0][0].shape}")
  print(f"Number of classes: {len(train_dataset.classes)}")

  return train_loader, valid_loader, test_loader


def SSC_dataloaders(config):
    set_seed(config.seed)

    train_dataset = BinnedSpikingSpeechCommands(
        config.datasets_path,
        config.n_bins,
        split="train",
        data_type="frame",
        duration=config.time_step,
    )
    valid_dataset = BinnedSpikingSpeechCommands(
        config.datasets_path,
        config.n_bins,
        split="valid",
        data_type="frame",
        duration=config.time_step,
    )
    test_dataset = BinnedSpikingSpeechCommands(
        config.datasets_path,
        config.n_bins,
        split="test",
        data_type="frame",
        duration=config.time_step,
    )

    train_loader = DataLoader(
        train_dataset,
        collate_fn=pad_sequence_collate,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=4,
    )
    valid_loader = DataLoader(
        valid_dataset,
        collate_fn=pad_sequence_collate,
        batch_size=config.batch_size,
        num_workers=4,
    )
    test_loader = DataLoader(
        test_dataset,
        collate_fn=pad_sequence_collate,
        batch_size=config.batch_size,
        num_workers=4,
    )

    return train_loader, valid_loader, test_loader


def GSC_dataloaders(config):
    set_seed(config.seed)

    train_dataset = GSpeechCommands(
        config.datasets_path,
        "training",
        transform=build_transform(False),
        target_transform=target_transform,
    )
    valid_dataset = GSpeechCommands(
        config.datasets_path,
        "validation",
        transform=build_transform(False),
        target_transform=target_transform,
    )
    test_dataset = GSpeechCommands(
        config.datasets_path,
        "testing",
        transform=build_transform(False),
        target_transform=target_transform,
    )

    train_loader = DataLoader(
        train_dataset, batch_size=config.batch_size, shuffle=True, num_workers=4
    )
    valid_loader = DataLoader(
        valid_dataset, batch_size=config.batch_size, num_workers=4
    )
    test_loader = DataLoader(test_dataset, batch_size=config.batch_size, num_workers=4)

    return train_loader, valid_loader, test_loader


class BinnedSpikingHeidelbergDigits(SpikingHeidelbergDigits):
    def __init__(
        self,
        root: str,
        n_bins: int,
        train: bool = None,
        data_type: str = "event",
        frames_number: int = None,
        split_by: str = None,
        duration: int = None,
        custom_integrate_function: Callable = None,
        custom_integrated_frames_dir_name: str = None,
        transform: Optional[Callable] = None,
        target_transform: Optional[Callable] = None,
    ) -> None:
        """
        The Spiking Heidelberg Digits (SHD) dataset, which is proposed by `The Heidelberg Spiking Data Sets for the Systematic Evaluation of Spiking Neural Networks <https://doi.org/10.1109/TNNLS.2020.3044364>`_.

        Refer to :class:`spikingjelly.datasets.NeuromorphicDatasetFolder` for more details about params information.

        .. admonition:: Note
            :class: note

            Events in this dataset are in the format of ``(x, t)`` rather than ``(x, y, t, p)``. Thus, this dataset is not inherited from :class:`spikingjelly.datasets.NeuromorphicDatasetFolder` directly. But their procedures are similar.

        :class:`spikingjelly.datasets.shd.custom_integrate_function_example` is an example of ``custom_integrate_function``, which is similar to the cunstom function for DVS Gesture in the ``Neuromorphic Datasets Processing`` tutorial.
        """
        super().__init__(
            root,
            train,
            data_type,
            frames_number,
            split_by,
            duration,
            custom_integrate_function,
            custom_integrated_frames_dir_name,
            transform,
            target_transform,
        )
        self.n_bins = n_bins

    def __getitem__(self, i: int):
        if self.data_type == "event":
            events = {
                "t": self.h5_file["spikes"]["times"][i],
                "x": self.h5_file["spikes"]["units"][i],
            }
            label = self.h5_file["labels"][i]
            if self.transform is not None:
                events = self.transform(events)
            if self.target_transform is not None:
                label = self.target_transform(label)

            return events, label

        elif self.data_type == "frame":
            frames = np.load(self.frames_path[i], allow_pickle=True)["frames"].astype(
                np.float32
            )
            label = self.frames_label[i]

            binned_len = frames.shape[1] // self.n_bins
            binned_frames = np.zeros((frames.shape[0], binned_len))
            for i in range(binned_len):
                binned_frames[:, i] = frames[
                    :, self.n_bins * i : self.n_bins * (i + 1)
                ].sum(axis=1)

            if self.transform is not None:
                binned_frames = self.transform(binned_frames)
            if self.target_transform is not None:
                label = self.target_transform(label)

            return binned_frames, label


class BinnedSpikingSpeechCommands(SpikingSpeechCommands):
    def __init__(
        self,
        root: str,
        n_bins: int,
        split: str = "train",
        data_type: str = "event",
        frames_number: int = None,
        split_by: str = None,
        duration: int = None,
        custom_integrate_function: Callable = None,
        custom_integrated_frames_dir_name: str = None,
        transform: Optional[Callable] = None,
        target_transform: Optional[Callable] = None,
    ) -> None:
        """
        The Spiking Speech Commands (SSC) dataset, which is proposed by `The Heidelberg Spiking Data Sets for the Systematic Evaluation of Spiking Neural Networks <https://doi.org/10.1109/TNNLS.2020.3044364>`_.

        Refer to :class:`spikingjelly.datasets.NeuromorphicDatasetFolder` for more details about params information.

        .. admonition:: Note
            :class: note

            Events in this dataset are in the format of ``(x, t)`` rather than ``(x, y, t, p)``. Thus, this dataset is not inherited from :class:`spikingjelly.datasets.NeuromorphicDatasetFolder` directly. But their procedures are similar.

        :class:`spikingjelly.datasets.shd.custom_integrate_function_example` is an example of ``custom_integrate_function``, which is similar to the cunstom function for DVS Gesture in the ``Neuromorphic Datasets Processing`` tutorial.
        """
        super().__init__(
            root,
            split,
            data_type,
            frames_number,
            split_by,
            duration,
            custom_integrate_function,
            custom_integrated_frames_dir_name,
            transform,
            target_transform,
        )
        self.n_bins = n_bins

    def __getitem__(self, i: int):
        if self.data_type == "event":
            events = {
                "t": self.h5_file["spikes"]["times"][i],
                "x": self.h5_file["spikes"]["units"][i],
            }
            label = self.h5_file["labels"][i]
            if self.transform is not None:
                events = self.transform(events)
            if self.target_transform is not None:
                label = self.target_transform(label)

            return events, label

        elif self.data_type == "frame":
            frames = np.load(self.frames_path[i], allow_pickle=True)["frames"].astype(
                np.float32
            )
            label = self.frames_label[i]

            binned_len = frames.shape[1] // self.n_bins
            binned_frames = np.zeros((frames.shape[0], binned_len))
            for i in range(binned_len):
                binned_frames[:, i] = frames[
                    :, self.n_bins * i : self.n_bins * (i + 1)
                ].sum(axis=1)

            if self.transform is not None:
                binned_frames = self.transform(binned_frames)
            if self.target_transform is not None:
                label = self.target_transform(label)

            return binned_frames, label


def build_transform(is_train):
    sample_rate = 16000
    window_size = 256
    hop_length = 80
    n_mels = 140
    f_min = 50
    f_max = 14000

    t = [
        augmentations.PadOrTruncate(sample_rate),
        Resample(sample_rate, sample_rate // 2),
    ]
    if is_train:
        t.extend(
            [
                augmentations.RandomRoll(dims=(1,)),
                augmentations.SpeedPerturbation(rates=(0.5, 1.5), p=0.5),
            ]
        )

    t.append(Spectrogram(n_fft=window_size, hop_length=hop_length, power=2))

    if is_train:
        pass

    t.extend(
        [
            MelScale(
                n_mels=n_mels,
                sample_rate=sample_rate // 2,
                f_min=f_min,
                f_max=f_max,
                n_stft=window_size // 2 + 1,
            ),
            AmplitudeToDB(),
        ]
    )

    return transforms.Compose(t)


def target_transform(word):
    return torch.tensor(labels.index(word))


class GSpeechCommands(Dataset):
    def __init__(
        self, root, split_name, transform=None, target_transform=None, download=True
    ):
        self.split_name = split_name
        self.transform = transform
        self.target_transform = target_transform
        self.dataset = SPEECHCOMMANDS(root, download=download, subset=split_name)

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        waveform, _, label, _, _ = self.dataset.__getitem__(index)

        if self.transform is not None:
            waveform = self.transform(waveform).squeeze().t()

        target = label

        if self.target_transform is not None:
            target = self.target_transform(target)

        return waveform, target, torch.zeros(1)
