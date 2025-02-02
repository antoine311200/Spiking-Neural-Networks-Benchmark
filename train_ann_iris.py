from datasets import SHD_dataloaders, SSC_dataloaders, GSC_dataloaders, IRIS_dataloaders
from config_ann_iris import Config
from snn_delays import SnnDelays
import torch
from ann import ANN
import utils



if __name__ == '__main__':
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n=====> Device = {device} \n\n")

    config = Config()

    model = ANN(config).to(device)


    if config.model_type == 'snn_delays_lr0':
        model.round_pos()


    print(f"===> Dataset    = {config.dataset}")
    print(f"===> Model type = {config.model_type}")
    print(f"===> Model size = {utils.count_parameters(model)}\n\n")


    train_loader, valid_loader, test_loader = IRIS_dataloaders(config)

    model.train_model(train_loader, valid_loader, test_loader, device)