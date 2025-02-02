from datasets import SHD_dataloaders, SSC_dataloaders, GSC_dataloaders, IRIS_dataloaders
from config_snn_iris import Config
from snn_delays import SnnDelays
import torch
from snn import SNN
import utils

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\n=====> Device = {device} \n\n")


        
        
for seed in range(5, 10):
    
    
    
    class ConfigSeed(Config):
        seed = seed
            
    config = ConfigSeed()
    print(f"===> Seed = {config.seed}")
    
    if config.model_type == 'snn':
        model = SNN(config).to(device)
    else:
        model = SnnDelays(config).to(device)

    if config.model_type == 'snn_delays_lr0':
        model.round_pos()


    print(f"===> Dataset    = {config.dataset}")
    print(f"===> Model type = {config.model_type}")
    print(f"===> Model size = {utils.count_parameters(model)}\n\n")


    if config.dataset == 'shd':
        train_loader, valid_loader = SHD_dataloaders(config)
        test_loader = None
    elif config.dataset == 'ssc':
        train_loader, valid_loader, test_loader = SSC_dataloaders(config)
    elif config.dataset == 'gsc':
        train_loader, valid_loader, test_loader = GSC_dataloaders(config)
    elif config.dataset == 'iris':
        train_loader, valid_loader, test_loader = IRIS_dataloaders(config)
    else:
        raise Exception(f'dataset {config.dataset} not implemented')

    if __name__ == '__main__':
        model.train_model(train_loader, valid_loader, test_loader, device)