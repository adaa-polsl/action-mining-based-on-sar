# Action mining based on survival action rules

This repository contains the code and data that were used for the action mining based on survival action rules.

## Requirements

To run content from `mutate.py` you need Python 3.10.12 or later. The list of required Python packages is in `requirements.txt`.

## Usage

```
python3 scripts/mutate.py --multirun fold=0,1,2,3,4,5,6,7,8,9 model=gbsa dataset=actg320,bmt-ch,cancer,FD001,FD002,FD003,FD004,follic,GBSG2,hd,lung,maintenance,Melanoma,mgus,pbc,PUL,std,uis,wcgs,whas1,whas500,zinc method=km hydra.launcher.n_jobs=8
```

## References

Hermansa, M.; Sikora, M.; Sikora, B.; Wróbel, Ł. *Action mining based on survival action rules*.
