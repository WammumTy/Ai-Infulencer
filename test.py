import torch
print(torch.cuda.is_available())        # should be True
print(torch.version.cuda)               # should be 11.8
print(torch.cuda.get_device_name(0))    # should be your 3060
